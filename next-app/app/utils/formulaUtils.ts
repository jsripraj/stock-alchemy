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

  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);
}
