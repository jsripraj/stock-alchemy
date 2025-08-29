"use client";

export default function Spreadsheet({
  dates,
  concepts,
}: {
  dates: string[];
  concepts: string[];
}) {
  return (
    <div>
      <table>
        <thead>
          <tr>
            <th
              scope="col"
              className="border border-[#a0a0a0] px-[10px] py-2"
            ></th>
            {dates.map((date) => (
              <th
                key={date}
                scope="col"
                className="border border-[#a0a0a0] px-[10px] py-2"
              >
                {date}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {concepts.map((concept) => (
            <tr key={concept}>
              <th
                scope="row"
                className="border border-[#a0a0a0] px-[10px] py-2"
              >
                {concept}
              </th>
              {dates.map((date) => (
                <td
                  key={date}
                  scope="row"
                  className="border border-[#a0a0a0] px-[10px] py-2"
                ></td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

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
    </div>
  );
}
