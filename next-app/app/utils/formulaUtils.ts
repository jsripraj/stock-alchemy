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

    // Check concepts
    const extractedConcepts = [...extractTokens(formula)];
    if (extractedConcepts.length === 0) {
      return {
        result: false,
        message: `Formula must contain at least one financial concept`,
      };
    }
    extractedConcepts.forEach((c) => {
      if (!getPrettyConceptText(c, dates, concepts)) {
        return { result: false, message: `Invalid financial concept: ${c}` };
      }
    });

    const unallowed = /[^0-9+\-*/()<>\s]/;
    const conceptRegex = /\[[^\]]+\]/g;

    // Normalize formula
    const normalized = formula.replaceAll(conceptRegex, "(1)");

    // Check for unallowed characters
    if (unallowed.test(normalized)) {
      return {
        result: false,
        message: "Invalid formula: unallowed characters",
      };
    }

    const sides = normalized.split(inequalityRegex);
    for (let i = 0; i < sides.length; i++) {
      const side = sides[i];
      const dir = i === 0 ? "left" : "right";

      // Check parsing
      if (!isParsable(side)) {
        return {
          result: false,
          message: `Invalid formula: unable to parse ${dir} side of inequality`,
        };
      }

      // Check for NaN and Infinity
      if (!Number.isFinite(evaluate(side))) {
        return {
          result: false,
          message: `Invalid formula: ${dir} side of inequality does not evaluate to a finite number`,
        };
      }
    }
  } catch {
    return { result: false, message: `Invalid formula` };
  }

  return { result: true, message: "" };
}

function isParsable(expr: string) {
  const isWhitespaceString = (str: string) => {
    return str.replace(/\s/g, "").length === 0;
  };
  if (isWhitespaceString(expr)) {
    return false;
  }

  const unallowed = /[^0-9+\-*/()\s]/;
  if (unallowed.test(expr)) {
    return false;
  }

  const numType = "num";
  const opType = "op";

  // Tokenize 
  let token = "";
  const tokenTypes = [];
  let i = 0;
  while (i < expr.length) {
    const char = expr[i];
    if (/\d/.test(char)) {
      // digit
      token += char;
    } else {
      // whitespace, operator, or parenthesis
      if (token) {
        tokenTypes.push(numType);
        token = "";
      }
      if (/[+\-*/]/.test(char)) {
        tokenTypes.push(opType);
      } else if (char === "(") {
        const end = expr.lastIndexOf(")");
        if (end <= i + 1 || !isParsable(expr.substring(i + 1, end))) {
          return false;
        }
        tokenTypes.push(numType);
        i = end + 1;
        continue;
      } else if (char === ")") {
        return false;
      }
    }
    i++;
  }
  if (token) {
    tokenTypes.push(numType);
  }

  // Check validity
  if (!tokenTypes.length) {
    return false;
  }
  for (i = 0; i < tokenTypes.length; i++) {
    const cur = tokenTypes[i];
    if ((i === 0 || i === tokenTypes.length - 1) && cur === "op") {
      return false;
    }
    if (i > 0) {
      const prev = tokenTypes[i-1];
      if (prev === cur) {
        return false;
      }
    }
  }

  return true;
}
