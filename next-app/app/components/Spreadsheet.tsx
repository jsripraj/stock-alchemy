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
    <div className="flex-2 overflow-auto mb-6">
      <table className="border-separate border-spacing-0">
        <thead>
          <tr>
            <th
              scope="col"
              className="border border-[#a0a0a0] px-[10px] py-2 sticky top-0 left-0 bg-white z-30"
            ></th>
            {dates.map((date, colIndex) => (
              <th
                key={date}
                scope="col"
                className={`border border-[#a0a0a0] px-[10px] py-2 sticky top-0 left-0 bg-white z-20 ${
                  hoverCol === colIndex ? "bg-yellow-100" : ""
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
                className={`border border-[#a0a0a0] px-[10px] py-2 sticky left-0 bg-white z-10 ${
                  hoverRow === rowIndex ? "bg-yellow-100" : ""
                }`}
              >
                {concept}
              </th>
              {dates.map((date, colIndex) => (
                <td
                  key={date}
                  scope="row"
                  className={`border border-[#a0a0a0] px-[10px] py-2 ${
                    hoverRow === rowIndex && hoverCol === colIndex
                      ? "bg-green-100"
                      : hoverRow === rowIndex || hoverCol === colIndex
                      ? "bg-yellow-100"
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