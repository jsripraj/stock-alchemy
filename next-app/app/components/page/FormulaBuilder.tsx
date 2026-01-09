"use client";

import React, { SetStateAction } from "react";
import { useRef, useEffect } from "react";
import {
  formatConcept,
  getCursorPos,
  restoreCursorPosition,
  getPrettyConceptText,
  getSpanParts,
} from "@/app/utils/formulaUtils";

export default function FormulaBuilder({
  formula,
  insertIntoFormula,
  setFormula,
  cursorPosRef,
  dates,
  concepts,
  errorMessage,
  isMessageVisable,
  findStocksClicked,
}: {
  formula: string;
  insertIntoFormula: (insertIndex: number, str: string) => void;
  setFormula: React.Dispatch<SetStateAction<string>>;
  cursorPosRef: React.RefObject<number>;
  dates: string[];
  concepts: string[];
  errorMessage: string;
  isMessageVisable: boolean;
  findStocksClicked: () => void;
}) {
  const unallowed = /[^A-Za-z0-9+\-*/()<>\[\]\s]/;
  const formulaDivRef = useRef<HTMLDivElement>(null);

  /* 
  Track changes to formula to add syntax highlighting, correct cursor positioning, 
  and prevent hidden characters.
  */
  useEffect(() => {
    if (!formulaDivRef.current) return;

    const cursorJump =
      formula.length - formulaDivRef.current.textContent.length;
    if (cursorJump > 0) {
      cursorPosRef.current += cursorJump;
    }

    // Highlight concepts
    while (formulaDivRef.current.firstChild) {
      formulaDivRef.current.removeChild(formulaDivRef.current.firstChild);
    }
    const parts = getSpanParts(formula);

    parts.forEach((p) => {
      const span = document.createElement("span");
      const concept = getPrettyConceptText(p, dates, concepts);

      if (concept) {
        span.textContent = concept;
        span.className = "text-lime-500";
      } else {
        span.textContent = p;
      }
      formulaDivRef.current?.appendChild(span);
    });

    // Restore cursor position
    restoreCursorPosition(formulaDivRef.current, cursorPosRef.current);
  }, [formula]);

  return (
    <div className="w-full flex-2 flex flex-col items-center mt-6 overflow-hidden">

      {/* Button bar */}
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
            onClick={() => {
              insertIntoFormula(cursorPosRef.current, op);
            }}
          >
            {op}
          </button>
        ))}
        <button
          className="px-3 py-1 bg-red-700 border border-red-500 rounded hover:bg-red-900 hover:font-semibold cursor-pointer font-medium text-red-50"
          onClick={() => {
            cursorPosRef.current = 0;
            setFormula("");
          }}
        >
          Clear
        </button>
      </div>

      {/* Formula editor area */}
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
        onBeforeInput={(e) => {
          const newlineRegex = /(\r\n|\r|\n)/
          if (newlineRegex.test(e.data)) {
            e.preventDefault();
            findStocksClicked();
          }
          if (unallowed.test(e.data)) {
            e.preventDefault();
          }
        }}
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
      ></div>

      {/* Invalid formula message */}
      <p
        className={`text-red-500 min-h-7 ${
          isMessageVisable ? "opacity-100" : "opacity-0"
        } transition-discrete transition-opacity duration-200`}
      >
        {errorMessage}
      </p>
    </div>
  );
}
