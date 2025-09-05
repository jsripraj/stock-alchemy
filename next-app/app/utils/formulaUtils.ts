export function formatConcept(words: string[]): string {
    return `[${words.join(" ")}]`;
}

export function extractTokens(formula: string): Set<string> {
    const regex = /\[[^\]]+\]/g;
    return new Set(formula.match(regex));
}