"use client";

import React, { useState } from 'react';
import { createEditor, BaseEditor, Descendant } from 'slate';
import { Slate, Editable, withReact, ReactEditor } from 'slate-react';

type CustomElement = { type: 'paragraph'; children: CustomText[] }
type CustomText = { text: string}

declare module 'slate' {
  interface CustomTypes {
    Editor: BaseEditor & ReactEditor
    Element: CustomElement
    Text: CustomText
  }
}

const initialValue = [
  {
    type: 'paragraph',
    children: [{ text: 'A line of text in a paragraph.' }],
  },
]

export default function FormulaBuilder() {
  const [editor] = useState(() => withReact(createEditor()));
  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Formula Builder</h2>
      {/* <div
        contentEditable
        className="mb-2 p-2 border border-gray-300 min-h-[40px]"
      >
        Click cells and type operators to build a formula
      </div> */}
      <Slate editor={editor} initialValue={initialValue} >
        <Editable />
      </Slate>
      <div className="flex flex-wrap gap-2 mb-2">
        {[...Array(10).keys()].map((n) => (
          <button key={n} className="px-3 py-1 bg-gray-200 rounded">
            {n}
          </button>
        ))}
        {["+", "-", "*", "/"].map((op) => (
          <button key={op} className="px-3 py-1 bg-blue-200 rounded">
            {op}
          </button>
        ))}
        <button className="px-3 py-1 bg-yellow-200 rounded">
          Add Selected Cell
        </button>
        <button className="px-3 py-1 bg-red-200 rounded">Clear</button>
      </div>
      <div>
        <strong>Result:</strong> my result
      </div>
    </div>
  );
}
