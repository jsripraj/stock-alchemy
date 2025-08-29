"use client";

export default function FormulaBuilder() {
  return (
    <div>
      <h2 className="text-xl font-bold mb-2">Formula Builder</h2>
      <div className="mb-2 p-2 border border-gray-300 min-h-[40px]">
        Click cells and type operators to build a formula
      </div>
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
