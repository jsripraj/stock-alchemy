import React from "react";
import { formatConcept } from "@/app/utils/formulaUtils";
import { fetchResults } from "@/app/utils/postgresUtils";
import { useRouter } from "next/navigation";


export default function FormulaBuilder({
  formula,
  setFormula,
}: {
  formula: string;
  setFormula: React.Dispatch<React.SetStateAction<string>>;
}) {
  const router = useRouter();

  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Formula Builder</h2>
      <div className="flex flex-wrap gap-2 mb-2">
        <button
          className="px-3 py-1 bg-yellow-200 rounded"
          onClick={() => setFormula((f) => f + formatConcept(["Market Cap"]))}
        >
          Market Cap
        </button>
        {[...Array(10).keys()].map((n) => (
          <button
            key={n}
            className="px-3 py-1 bg-gray-200 rounded"
            onClick={() => setFormula((f) => f + n.toString())}
          >
            {n}
          </button>
        ))}
        {["+", "-", "*", "/", "(", ")", "<", ">"].map((op) => (
          <button
            key={op}
            className="px-3 py-1 bg-blue-200 rounded"
            onClick={() => setFormula((f) => f + op)}
          >
            {op}
          </button>
        ))}
        <button
          className="px-3 py-1 bg-red-200 rounded"
          onClick={() => setFormula((f) => "")}
        >
          Clear
        </button>
      </div>
      <div className="mb-2 p-2 border border-gray-300 min-h-[40px]">
        {formula}
      </div>
      <button
        className="px-3 py-1 bg-green-200 rounded"
        onClick={ () => {
          // check formula
          // store formula in db, get db ID
          // push results page, with db ID in URL params
          router.push("/results");
        }}
      >
        Find Stocks
      </button>
    </div>
  );
}
