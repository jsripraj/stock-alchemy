import { simplify } from "mathjs";
import { fetchResults } from "@/app/utils/postgresUtils";

export function formatConcept(words: string[]): string {
  return `[${words.join(" ")}]`;
}

export function getPrettyConceptText(
  str: string,
  dates: string[],
  concepts: string[]
): string | null {
  if (str.startsWith("[") && str.endsWith("]")) {
    const subLower = str.substring(1, str.length - 1).toLowerCase();
    if (subLower === "market cap") {
      return "[Market Cap]";
    }
    const firstSpaceIndex = subLower.indexOf(" ");
    const year = subLower.substring(0, firstSpaceIndex);
    const concept = subLower
      .substring(firstSpaceIndex + 1)
      .replaceAll("-", " ");
    const conceptsLowerCase = concepts.map((c) =>
      c.toLowerCase().replaceAll("-", " ")
    );
    if (dates.includes(year)) {
      const i = conceptsLowerCase.indexOf(concept);
      if (i !== -1) {
        return `[${year} ${concepts[i]}]`;
      }
    }
  }
  return null;
}

export function getMostRecentYear() {
  return new Date().getFullYear() - 1;
}

export function getCursorPos(formulaDivRef: HTMLDivElement | null) {
  const selection = window.getSelection();
  if (!formulaDivRef || !selection || selection.rangeCount === 0) return 0;
  const range = selection.getRangeAt(0);
  const cloneRange = range.cloneRange();
  cloneRange.selectNodeContents(formulaDivRef);
  cloneRange.setEnd(range.endContainer, range.endOffset);
  return cloneRange.toString().length;
}

export function restoreCursorPosition(
  container: HTMLElement,
  cursorPos: number
) {
  const selection = window.getSelection();
  if (!selection) return;

  const range = document.createRange();

  let pos = cursorPos;
  let node: ChildNode | null = container.firstChild;

  if (node) {
    while (node) {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent ?? "";
        if (pos <= text.length) {
          range.setStart(node, pos);
          break;
        } else {
          pos -= text.length;
        }
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        // Walk into the element
        const text = node.textContent ?? "";
        if (pos <= text.length) {
          node = node.firstChild;
          continue;
        } else {
          pos -= text.length;
        }
      }
      node = node.nextSibling;
    }
  } else {
    range.setStart(container, pos);
  }

  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);
}

function capitalizeFirstLetter(word: string): string {
  if (!word) return word;
  const chars = word.split("");
  chars[0] = chars[0].toUpperCase();
  return chars.join("");
}

function extractConceptName(token: string): string {
  const bracketsRegex = /[\[\]]/g;
  const words = token.replaceAll(bracketsRegex, "").split(" ");
  return words
    .slice(1)
    .map((word) => capitalizeFirstLetter(word))
    .join("");
}

function extractYear(token: string): string {
  const bracketsRegex = /[\[\]]/g;
  const words = token.replaceAll(bracketsRegex, "").split(" ");
  return words[0];
}
export function extractTokens(formula: string): Set<string> {
  const regex = /\[[^\]]+\]/g;
  return new Set(formula.match(regex));
}

function getSqlName(token: string): string {
  if (token === "[Market Cap]") {
    return "MarketCap";
  }
  const year = extractYear(token);
  const concept = extractConceptName(token);
  return `${concept}${year}`;
}

function getSqlSelectTerm(token: string, mostRecentYear: string): string {
  if (token === "[Market Cap]") {
    return `(companies.close * ${getSqlSelectTerm(
      "[2024 Shares Outstanding]",
      mostRecentYear
    )})`;
  }
  return `${getSqlName(token)}.value`;
}

function getSqlJoinStatement(token: string, mostRecentYear: string): string {
  if (token === "[Market Cap]") {
    return getSqlJoinStatement(
      `[${mostRecentYear} Shares Outstanding]`,
      mostRecentYear
    );
  }
  const concept = getSqlName(token);
  return `join financials ${concept} on companies.cik = ${concept}.cik
            and ${concept}.concept = '${extractConceptName(token)}'
            and ${concept}.year = ${extractYear(token)}
            and ${concept}.period = 'Q4'
            and (${concept}.duration = 'Year' or ${concept}.duration is null)`;
}

function getSqlSelectExpression(
  formula: string,
  tokens: Set<string>,
  mostRecentYear: string
) {
  tokens.forEach((token) => {
    formula = formula.replaceAll(
      token,
      getSqlSelectTerm(token, mostRecentYear)
    );
  });
  return formula;
}

export function getSqlQuery(
  formula: string,
  mostRecentYear: string,
  limit: number = 0
) {
  const tokens = extractTokens(formula);

  const regex = /(.+)(<|>)(.+)/;
  const match = formula.match(regex);

  if (!match) return null;

  const [, leftFormula, compOperator, rightFormula] = match.map((s) =>
    s.trim()
  );
  const leftSelect = getSqlSelectExpression(
    leftFormula,
    tokens,
    mostRecentYear
  );
  const rightSelect = getSqlSelectExpression(
    rightFormula,
    tokens,
    mostRecentYear
  );
  const joinStatements = [...tokens].map((token) =>
    getSqlJoinStatement(token, mostRecentYear)
  );
  const limitStatement = limit > 0 ? `limit ${limit}` : "";

  return `
    with results as (
        select
            companies.ticker, 
            companies.company,
            ${leftSelect} as leftSide,
            ${rightSelect} as rightSide
        from companies
        ${joinStatements.join("\n")}
        ${limitStatement}
    )  
    select *
    from results
    where leftSide ${compOperator} rightSide;
  `;
}

export async function isValidFormula(
  formula: string,
  dates: string[],
  trueConcepts: string[]
): Promise<{ result: boolean; message: string }> {
  try {
    // Check inequality
    const inequalityRegex = /[<>]/g;
    const matches = formula.match(inequalityRegex);
    if (!matches?.length) {
      return {
        result: false,
        message: `The formula must be an inequality and include one of "<" or ">"`,
      };
    }
    if (matches.length > 1) {
      return { result: false, message: `Too many inequality operators` };
    }
    const inequality = matches[0];

    // Check concepts
    const extractedConcepts = [...extractTokens(formula)];
    if (extractedConcepts.length === 0) {
      return {
        result: false,
        message: `Formula must contain at least one financial concept`,
      };
    }
    for (const c of extractedConcepts) {
      if (!getPrettyConceptText(c, dates, trueConcepts)) {
        return { result: false, message: `Invalid financial concept: ${c}` };
      }
    }

    // Check for unallowed characters outside of concepts
    const unallowed = /[^0-9+\-*/()<>\s]/;
    const dummyFormula = replaceConceptsWithDummyVar(
      formula,
      extractedConcepts
    );
    if (dummyFormula.match(unallowed)) {
      return {
        result: false,
        message: `Invalid Formula: Unexpected characters.`,
      };
    }

    // Normalize formula
    const formulaWithIDs = replaceConceptsWithIDs(formula, extractedConcepts);

    // Check if each side evaluates to infinity
    const sides = formulaWithIDs.split(inequality);
    const leftSideSimplified = simplify(sides[0]).toString();
    if (leftSideSimplified.includes("Infinity")) {
      return {
        result: false,
        message: `Invalid formula: left side of inequality does not evaluate to a finite number`,
      };
    }
    const rightSideSimplified = simplify(sides[1]).toString();
    if (rightSideSimplified.includes("Infinity")) {
      return {
        result: false,
        message: `Invalid formula: right side of inequality does not evaluate to a finite number`,
      };
    }

    // Check each side for implicit multiplication
    const hasImplicitMultiplication = (expr: string) => {
      const trimParens = (str: string) => {
        const parensRegex = /[\(\)]/g;
        return str.replace(parensRegex, "");
      };

      const getType = (term: string) => {
        const opsRegex = /[\+\-\*/\^]/g; // include ^ operator because math.simplify may insert it
        if (trimParens(term).match(opsRegex)) {
          return "op";
        }
        return "num";
      };

      const terms = expr.split(" ");
      let prevType = null;
      let curType = null;
      for (const term of terms) {
        curType = getType(term);
        if (prevType === "num" && curType === "num") {
          return true;
        }
        prevType = curType;
      }
      return false;
    };

    if (hasImplicitMultiplication(leftSideSimplified)) {
      return {
        result: false,
        message: `Invalid formula: Make sure to use explicit multiplication operators (*) on left side of inequality.`,
      };
    }
    if (hasImplicitMultiplication(rightSideSimplified)) {
      return {
        result: false,
        message: `Invalid formula: Make sure to use explicit multiplication operators (*) on right side of inequality.`,
      };
    }

    // Check if formula evaluates to a boolean
    const formulaWithIDsSimplified = simplify(formulaWithIDs).toString();
    if (formulaWithIDsSimplified === "0" || formulaWithIDsSimplified === "1") {
      return {
        result: false,
        message: `Invalid formula: Evaluates to boolean ${
          formulaWithIDsSimplified === "1" ? "True" : "False"
        }`,
      };
    }

    // Lastly, check if Postgres is okay with the query translated from the formula
    await fetchResults(formula, getMostRecentYear().toString(), 1);

    return {
      result: true,
      message: "",
    };
  } catch {
    return { result: false, message: `Invalid formula` };
  }
}

function getConcepts(formula: string): string[] {
  const conceptRegex = /\[[^\]]+\]/g;
  const concepts = formula
    .matchAll(conceptRegex)
    .map((match: string[]) => match[0]);
  return [...concepts];
}

export function getSpanParts(formula: string): string[] {
  const parts = formula.split(/(\[[^\]]+\])/g).filter((p) => p !== "");
  return parts;
}

function replaceConceptsWithDummyVar(formula: string, concepts: string[]) {
  const dummy = "(1)";
  let replaced = formula;
  concepts.forEach((c) => {
    replaced = replaced.replaceAll(c, dummy);
  });

  return replaced;
}

function replaceConceptsWithIDs(formula: string, concepts: string[]) {
  // const conceptRegex = /\[[^\]]+\]/g;
  // const concepts = formula
  //   .matchAll(conceptRegex)
  //   .map((match: string[]) => match[0]);
  // const concepts = getConcepts(formula);

  let num = 1;
  const getID = () => {
    return "x" + (num++).toString();
  };

  const conceptToID = new Map();
  concepts.forEach((c) => {
    if (!conceptToID.has(c)) {
      conceptToID.set(c, getID());
    }
  });

  let replaced = formula;
  conceptToID.forEach((id, concept) => {
    replaced = replaced.replaceAll(concept, `(${id})`);
  });

  return replaced;
}
