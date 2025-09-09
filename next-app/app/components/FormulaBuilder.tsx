import React from "react";
import { formatConcept } from "@/app/utils/formulaUtils";

export default function FormulaBuilder({
  formula,
  setFormula,
}: {
  formula: string;
  setFormula: React.Dispatch<React.SetStateAction<string>>;
}) {
  return (
    <div className="w-full flex-2 flex flex-col items-center overflow-hidden">
      <h2 className="text-xl font-bold mb-2">Formula Builder</h2>
      <div className="flex gap-2 mb-2">
        <button
          className="px-3 py-1 bg-yellow-200 rounded hover:bg-yellow-300 cursor-pointer"
          onClick={() => setFormula((f) => f + formatConcept(["Market Cap"]))}
        >
          Market Cap
        </button>
        {[...Array(10).keys()].map((n) => (
          <button
            key={n}
            className="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 cursor-pointer"
            onClick={() => setFormula((f) => f + n.toString())}
          >
            {n}
          </button>
        ))}
        {["+", "-", "*", "/", "(", ")", "<", ">"].map((op) => (
          <button
            key={op}
            className="px-3 py-1 bg-blue-200 rounded hover:bg-blue-300 cursor-pointer"
            onClick={() => setFormula((f) => f + op)}
          >
            {op}
          </button>
        ))}
        <button
          className="px-3 py-1 bg-red-200 rounded hover:bg-red-300 cursor-pointer"
          onClick={() => setFormula((f) => "")}
        >
          Clear
        </button>
      </div>
      <div className="w-full h-1/2 mb-2 border border-gray-300 overflow-y-auto flex justify-center">
        {formula}
      </div>
    </div>
  );
}