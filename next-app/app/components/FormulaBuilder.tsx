"use client";

import React, { SetStateAction } from "react";
import { useRef, useEffect } from "react";
import { formatConcept, getCursorPos, restoreCursorPosition } from "@/app/utils/formulaUtils";

export default function FormulaBuilder({
  formula,
  insertIntoFormula,
  setFormula,
  cursorPosRef,
}: {
  formula: string;
  insertIntoFormula: (insertIndex: number, str: string) => void;
  setFormula: React.Dispatch<SetStateAction<string>>;
  cursorPosRef: React.RefObject<number>;
}) {
  const formulaDivRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!formulaDivRef.current) return;

    const cursorJump =
      formula.length - formulaDivRef.current.textContent.length;
    console.log(`jump: ${cursorJump}`)
    if (cursorJump > 0) {
      cursorPosRef.current += cursorJump;
    }

    // Parse formula
    const parts = formula.split(/(\[[^\]]+\])/g).filter((p) => p !== "");
    while (formulaDivRef.current.firstChild) {
      formulaDivRef.current.removeChild(formulaDivRef.current.firstChild);
    }
    parts.forEach((p) => {
      const span = document.createElement("span");
      span.textContent = p;
      if (p.startsWith("[")) {
        span.className = "text-lime-500";
      }
      formulaDivRef.current?.appendChild(span);
    });

    // Restore cursor position
    restoreCursorPosition(formulaDivRef.current, cursorPosRef.current);
  }, [formula]);

  return (
    <div className="w-full flex-2 flex flex-col items-center my-6 overflow-hidden">
      <div className="flex gap-2 mb-2">
        <button
          className="px-3 py-1 bg-black border border-lime-500 rounded hover:bg-lime-900 hover:font-semibold cursor-pointer font-medium text-lime-50"
          onClick={() =>
            insertIntoFormula(
              cursorPosRef.current,
              formatConcept(["Market Cap"])
            )
          }
        >
          Market Cap
        </button>
        {[...Array(10).keys()].map((n) => (
          <button
            key={n}
            className="px-3 py-1 bg-black border border-yellow-500 rounded hover:bg-yellow-900 hover:font-semibold cursor-pointer font-medium text-yellow-50"
            onClick={() =>
              insertIntoFormula(cursorPosRef.current, n.toString())
            }
          >
            {n}
          </button>
        ))}
        {["+", "-", "*", "/", "(", ")", "<", ">"].map((op) => (
          <button
            key={op}
            className="px-3 py-1 bg-black border border-orange-500 rounded hover:bg-orange-900 hover:font-semibold cursor-pointer font-medium text-orange-50"
            onClick={() => insertIntoFormula(cursorPosRef.current, op)}
          >
            {op}
          </button>
        ))}
        <button
          className="px-3 py-1 bg-red-700 border border-red-500 rounded hover:bg-red-900 hover:font-semibold cursor-pointer font-medium text-red-50"
          onClick={() => setFormula("")}
        >
          Clear
        </button>
      </div>
      <div
        ref={formulaDivRef}
        className="w-full flex-1 mb-2 p-2 
          border border-lime-500 focus:border-2 focus:border-lime-400 rounded-xs outline-none 
          overflow-y-auto 
          text-lime-50 text-lg font-mono 
          scrollbar scrollbar-thumb-stone-600 scrollbar-track-lime-500
        "
        contentEditable={true}
        autoFocus={true}
        onInput={(e) => {
          cursorPosRef.current = getCursorPos(formulaDivRef.current);
          setFormula(
            e.currentTarget?.textContent ? e.currentTarget.textContent : ""
          );
        }}
        onKeyUp={() => {
          cursorPosRef.current = getCursorPos(formulaDivRef.current);
        }}
        onClick={() => {
          cursorPosRef.current = getCursorPos(formulaDivRef.current);
        }}
      >
      </div>
    </div>
  );
}
