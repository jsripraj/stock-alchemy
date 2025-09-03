"use client";

import React, { useState } from "react";
import { createEditor, BaseEditor, Descendant } from "slate";
import { Slate, Editable, withReact, ReactEditor } from "slate-react";

type CustomElement = { type: "paragraph"; children: CustomText[] };
type CustomText = { text: string };

declare module "slate" {
  interface CustomTypes {
    Editor: BaseEditor & ReactEditor;
    Element: CustomElement;
    Text: CustomText;
  }
}

const initialValue: Descendant[] = [
  {
    type: "paragraph",
    children: [{ text: "A line of text in a paragraph." }],
  },
];

export default function FormulaBuilder({
  formula,
  appendToFormula,
}: {
  formula: string;
  appendToFormula: (s: string) => void;
}) {
  const [editor] = useState(() => withReact(createEditor()));

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Formula Builder</h2>
      <div className="flex flex-wrap gap-2 mb-2">
        {[...Array(10).keys()].map((n) => (
          <button
            key={n}
            className="px-3 py-1 bg-gray-200 rounded"
            onClick={() => appendToFormula(n.toString())}
          >
            {n}
          </button>
        ))}
        {["+", "-", "*", "/"].map((op) => (
          <button key={op} className="px-3 py-1 bg-blue-200 rounded" onClick={() => appendToFormula(op)}>
            {op}
          </button>
        ))}
        {/* <button className="px-3 py-1 bg-yellow-200 rounded">
          Add Selected Cell
        </button> */}
        {/* <button className="px-3 py-1 bg-red-200 rounded">Clear</button> */}
      </div>
      <div className="mb-2 p-2 border border-gray-300 min-h-[40px]">
        {formula}
      </div>
    </div>
  );
}
