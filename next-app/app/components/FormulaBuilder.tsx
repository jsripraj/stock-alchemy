"use client";

import React from "react";
import { useRef, useEffect } from "react";
import { formatConcept } from "@/app/utils/formulaUtils";

export default function FormulaBuilder({
  formula,
  setFormula,
}: {
  formula: string;
  setFormula: React.Dispatch<React.SetStateAction<string>>;
}) {
  const formulaDivRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // parse formula and update formulaDivRef
    const selection = window.getSelection();
    const cursorPos = selection?.getRangeAt(0).startOffset ?? 0;

    if (formulaDivRef.current) {
      formulaDivRef.current.textContent = formula;
    }

    // Restore cursor's original position
    if (selection && formulaDivRef.current?.firstChild) {
      const range = document.createRange();
      const firstChild = formulaDivRef.current.firstChild;
      const pos = Math.min(cursorPos, formulaDivRef.current.textContent?.length ?? 0);
      range.setStart(firstChild, pos);
      range.collapse(true);
      selection.removeAllRanges();
      selection.addRange(range);
    }
  }, [formula]);

  // const handleInput = (e: React.FormEvent<HTMLDivElement>) => {};

  return (
    <div className="w-full flex-2 flex flex-col items-center my-6 overflow-hidden">
      <div className="flex gap-2 mb-2">
        <button
          className="px-3 py-1 bg-black border border-lime-500 rounded hover:bg-lime-900 hover:font-semibold cursor-pointer font-medium text-lime-50"
          onClick={() => setFormula((f) => f + formatConcept(["Market Cap"]))}
        >
          Market Cap
        </button>
        {[...Array(10).keys()].map((n) => (
          <button
            key={n}
            className="px-3 py-1 bg-black border border-yellow-500 rounded hover:bg-yellow-900 hover:font-semibold cursor-pointer font-medium text-yellow-50"
            onClick={() => setFormula((f) => f + n.toString())}
          >
            {n}
          </button>
        ))}
        {["+", "-", "*", "/", "(", ")", "<", ">"].map((op) => (
          <button
            key={op}
            className="px-3 py-1 bg-black border border-orange-500 rounded hover:bg-orange-900 hover:font-semibold cursor-pointer font-medium text-orange-50"
            onClick={() => setFormula((f) => f + op)}
          >
            {op}
          </button>
        ))}
        <button
          className="px-3 py-1 bg-red-700 border border-red-500 rounded hover:bg-red-900 hover:font-semibold cursor-pointer font-medium text-red-50"
          onClick={() => setFormula((f) => "")}
        >
          Clear
        </button>
      </div>
      <div
        ref={formulaDivRef}
        className="w-full flex-1 mb-2 p-2 
          border border-lime-500 focus:border-2 focus:border-lime-400 rounded-xs outline-none 
          overflow-y-auto flex justify-center 
          text-lime-50 text-lg font-mono 
          scrollbar scrollbar-thumb-stone-600 scrollbar-track-lime-500
        "
        contentEditable={true}
        autoFocus={true}
        onInput={(e) => {
          setFormula(
            e.currentTarget && e.currentTarget.textContent
              ? e.currentTarget.textContent
              : " "
          );
        }}
        // onInput={(e) => {
        //   if (formulaDivRef.current) {
        //     const span = document.createElement("span");
        //     span.textContent = "hello world";
        //     span.className = "text-3xl";
        //     formulaDivRef.current.appendChild(span);
        //   }
        // }}
      >
        {/* <span>hello&nbsp;</span><span className="text-red-500">extra large</span> world */}
      </div>
    </div>
  );
}
