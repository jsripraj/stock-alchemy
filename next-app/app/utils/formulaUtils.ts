export function formatConcept(words: string[]): string {
    return `[${words.join(" ")}]`;
}

export function extractTokens(formula: string): Set<string> {
    const regex = /\[[^\]]+\]/g;
    return new Set(formula.match(regex));
}

export function getSqlSelectTerm(token: string, mostRecentYear: string): string {
    if (token === "[Market Cap]") {
        return `(companies.close * sharesOutstanding${mostRecentYear}.value)`
    }
    const bracketsRegex = /[\[\]]/g;
    const words = token.replaceAll(bracketsRegex, "").split(" ");
    const year = words[0];
    const concept= words.slice(1).join("");
    return `${concept}${year}.value`;
}