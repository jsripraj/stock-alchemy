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

  const headers = ["Ticker", "Company", "Left Side", "Right Side"];
  const spanParts = getSpanParts(formula);

  return (
    <div className="w-8/10 flex flex-col items-center overflow-hidden">

      {/* Formula area */}
      <label className="text-lime-500 text-lg font-mono">Formula</label>
      <div
        className="w-full min-h-30 mb-8 p-2 
          border border-lime-500 rounded-xs outline-none 
          overflow-y-auto 
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
      <table className="border-separate border-spacing-0">
        <thead>
          <tr>
            {headers.map((h) => (
              <th
                key={h}
                scope="col"
                className={`border border-[#a0a0a0] px-[10px] py-2 sticky top-0 left-0 bg-white z-20`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {results.map((res) => (
            <tr key={res.ticker}>
              {Object.entries(res).map(([key, value]) => (
                <td
                  key={key}
                  scope="row"
                  className={`border border-[#a0a0a0] px-[10px] py-2 text-lime-500`}
                >
                  {value}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
