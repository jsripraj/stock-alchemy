import { fetchResults, fetchFormula } from "@/app/utils/postgresUtils";
import {
  getMostRecentYear,
  getSpanParts,
  getPrettyConceptText,
} from "@/app/utils/formulaUtils";

interface ResultsPageProps {
  searchParams: { id?: string };
}

export default async function ResultsPage({ searchParams }: ResultsPageProps) {
  const sp = await searchParams;
  const formulaId = sp.id;
  const noResults = <p>No Results</p>;

  if (!formulaId) {
    return noResults;
  }
  const [{ formula }] = await fetchFormula(formulaId);
  if (!formula) {
    return noResults;
  }
  const results = await fetchResults(formula, getMostRecentYear().toString());
  if (!results) {
    return noResults;
  }
  
  const leftSideMinAbs = Math.min(...(results.map((r) => Math.abs(r.leftside))));
  const rightSideMinAbs = Math.min(...(results.map((r) => Math.abs(r.rightside))));
  const getFormatter = (minAbs: number) => {
    if (minAbs < 1.0) {
      return ((x: Number) => {return x.toPrecision(4)});
    }
    if (minAbs < 1000) {
      return (x: Number) => {
        return x.toFixed(2)
      };
    }
    return (x: Number) => {return x.toFixed(0)};
  }
  const leftFormatter = getFormatter(leftSideMinAbs);
  const rightFormatter = getFormatter(rightSideMinAbs);

  const headers = ["Ticker", "Company", "Left Side", "Right Side"];
  const spanParts = getSpanParts(formula);

  return (
    <div className="w-8/10 flex flex-col items-center overflow-hidden">

      {/* Formula area */}
      <label className="text-lime-500 text-lg font-mono">Formula</label>
      <div
        className="w-full min-h-12 mb-6 p-2 
          border border-lime-500 rounded-xs outline-none 
          overflow-y-auto resize-y
          text-lime-50 text-lg font-mono 
          scrollbar scrollbar-thumb-stone-600 scrollbar-track-lime-500
        "
      >
        {spanParts.map((p, i) => {
          return p.startsWith("[") ? (
            <span key={i} className="text-lime-500">
              {p}
            </span>
          ) : (
            <span key={i}>{p}</span>
          );
        })}
      </div>

      {/* Results table */}
      <label className="text-lime-500 text-lg font-mono">{`Results (${results.length})`}</label>
      <div className="flex-2 border border-lime-500 rounded-xs overflow-auto mb-6 border scrollbar scrollbar-thumb-stone-600 scrollbar-track-lime-500">
        <table className="border-separate border-spacing-0 text-lime-100">
          <thead>
            <tr>
              {headers.map((h) => (
                <th
                  key={h}
                  scope="col"
                  className={"border border-lime-500 px-3 py-1 sticky top-0 left-0 bg-[var(--background)] z-20"}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {results.map((res) => (
              <tr key={res.ticker}>
                {Object.entries(res).map(([key, value]) => {
                  let formattedValue = value;
                  if (key === "leftside") {
                    formattedValue = leftFormatter(Number(value));
                  } else if (key === "rightside") {
                    formattedValue = rightFormatter(Number(value));
                  } 
                   return (
                  <td
                    key={key}
                    scope="row"
                    className={"border border-lime-500 px-3 py-1"}
                  >
                    {formattedValue}
                  </td>
                )})}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
