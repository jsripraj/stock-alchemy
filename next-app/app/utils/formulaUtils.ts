export function formatConcept(words: string[]): string {
  return `[${words.join(" ")}]`;
}

function extractTokens(formula: string): Set<string> {
  const regex = /\[[^\]]+\]/g;
  return new Set(formula.match(regex));
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

function getSqlName(token: string): string {
  if (token === "[Market Cap]") {
    return "MarketCap";
  }
  const year = extractYear(token);
  const concept = extractConceptName(token);
  return `${concept}${year}`;
}

function getSqlSelectTerm(
  token: string,
  mostRecentYear: string
): string {
  if (token === "[Market Cap]") {
    return `(companies.close * ${getSqlSelectTerm(
      "[2024 Shares Outstanding]",
      mostRecentYear
    )})`;
  }
  return `${getSqlName(token)}.value`;
}

function getSqlJoinStatement(
  token: string,
  mostRecentYear: string
): string {
  if (token === "[Market Cap]") {
    return getSqlJoinStatement(`[${mostRecentYear} Shares Outstanding]`, mostRecentYear);
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
