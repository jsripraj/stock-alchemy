export default function FormulaBuilder({
  formula,
  appendToFormula,
}: {
  formula: string;
  appendToFormula: (s: string) => void;
}) {
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
        {["+", "-", "*", "/", "<", ">"].map((op) => (
          <button
            key={op}
            className="px-3 py-1 bg-blue-200 rounded"
            onClick={() => appendToFormula(op)}
          >
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
