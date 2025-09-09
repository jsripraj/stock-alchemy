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
      <div className="w-full flex-1 mb-2 border border-lime-500 rounded-xs overflow-y-auto flex justify-center text-lime-50 scrollbar scrollbar-thumb-stone-600 scrollbar-track-lime-500">
        {formula}
      </div>
    </div>
  );
}
