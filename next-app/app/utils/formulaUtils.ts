import { evaluate } from "mathjs";

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
    const spaceIndex = subLower.indexOf(" ");
    const year = subLower.substring(0, spaceIndex);
    const concept = subLower.substring(spaceIndex + 1).replaceAll("-", " ");
    const conceptsLowerCase = concepts.map((c) =>
      c.toLowerCase().replaceAll("-", " ")
    );
    if (dates.includes(year)) {
      const i = conceptsLowerCase.indexOf(concept);
      if (i !== 0) {
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

export function getSqlQuery(formula: string, mostRecentYear: string) {
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

  return `
    with results as (
        select
            companies.ticker, 
            companies.company,
            ${leftSelect} as leftSide,
            ${rightSelect} as rightSide
        from companies
        ${joinStatements.join("\n")}
    )  
    select *
    from results
    where leftSide ${compOperator} rightSide;
  `;
}
export function isValidFormula(
  formula: string,
  dates: string[],
  concepts: string[]
): { result: boolean; message: string } {

  // Check concepts
  const extractedConcepts = [...extractTokens(formula)];
  if (extractedConcepts.length === 0) {
    return { result: false, message: `Formula must contain at least one financial concept` };
  }
  extractedConcepts.forEach((c) => {
    if (!getPrettyConceptText(c, dates, concepts)) {
      return { result: false, message: `Invalid financial concept: ${c}` };
    }
  });

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

  // Replace concepts with "1 "
  const conceptRegex = /\[[^\]]+\]/g;
  const normalized = formula.replaceAll(conceptRegex, "1 ");

  // Check if normalized formula is valid
  const unallowed = /[^0-9+\-*/()\s]/;
  const sides = normalized.split(inequalityRegex);
  for (const side of sides) {
    try {
      if (unallowed.test(side)) {
        throw new Error("Invalid formula");
      }
      const test = evaluate(side);
      if (!Number.isFinite(test)) {
        throw new Error("Invalid formula");
      }
    } catch {
      return { result: false, message: `Invalid formula` };
    }
  }

  return { result: true, message: "" };
}
