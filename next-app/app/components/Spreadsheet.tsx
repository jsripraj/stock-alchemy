"use client";

import React, { useState } from "react";
import { formatConcept } from "@/app/utils/formulaUtils";

export default function Spreadsheet({
  dates,
  concepts,
  setFormula,
}: {
  dates: string[];
  concepts: string[];
  setFormula: React.Dispatch<React.SetStateAction<string>>;
}) {
  const [hoverRow, setHoverRow] = useState<number | null>(null);
  const [hoverCol, setHoverCol] = useState<number | null>(null);

  return (
    <div className="flex-2 border border-lime-500 overflow-auto mb-6 border scrollbar scrollbar-thumb-stone-600 scrollbar-track-lime-500">
      <table className="border-separate border-spacing-0 text-lime-50">
        <thead>
          <tr>
            <th
              scope="col"
              className="border border-lime-500 px-3 py-1 sticky top-0 left-0 bg-[var(--background)] z-30"
            ></th>
            {dates.map((date, colIndex) => (
              <th
                key={date}
                scope="col"
                className={`border border-lime-500 px-3 py-1 sticky top-0 left-0 bg-[var(--background)] z-20 ${
                  hoverCol === colIndex ? "bg-lime-900" : ""
                }`}
              >
                {date}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {concepts.map((concept, rowIndex) => (
            <tr key={concept}>
              <th
                scope="row"
                className={`border border-lime-500 px-3 py-1 sticky left-0 bg-[var(--background)] z-10 ${
                  hoverRow === rowIndex ? "bg-lime-900" : ""
                }`}
              >
                {concept}
              </th>
              {dates.map((date, colIndex) => (
                <td
                  key={date}
                  scope="row"
                  className={`border border-lime-500 px-3 py-1 ${
                    hoverRow === rowIndex && hoverCol === colIndex
                      ? "bg-lime-500"
                      : hoverRow === rowIndex || hoverCol === colIndex
                      ? "bg-lime-900"
                      : ""
                  }`}
                  onMouseEnter={() => {
                    setHoverRow(rowIndex);
                    setHoverCol(colIndex);
                  }}
                  onMouseLeave={() => {
                    setHoverRow(null);
                    setHoverCol(null);
                  }}
                  onClick={() => {
                    setFormula(
                      (f) =>
                        f + formatConcept([dates[colIndex], concepts[rowIndex]])
                    );
                  }}
                ></td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}