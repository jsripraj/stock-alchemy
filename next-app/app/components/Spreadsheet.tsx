"use client";

import { useState } from "react";

export default function Spreadsheet({
  dates,
  concepts,
  appendToFormula,
}: {
  dates: string[];
  concepts: string[];
  appendToFormula: (s: string) => void;
}) {
  const [hoverRow, setHoverRow] = useState<number | null>(null);
  const [hoverCol, setHoverCol] = useState<number | null>(null);

  return (
    <div className="overflow-scroll">
      <table>
        <thead>
          <tr>
            <th
              scope="col"
              className="border border-[#a0a0a0] px-[10px] py-2"
            ></th>
            {dates.map((date, colIndex) => (
              <th
                key={date}
                scope="col"
                className={`border border-[#a0a0a0] px-[10px] py-2 ${
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
                className={`border border-[#a0a0a0] px-[10px] py-2 ${
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
                    appendToFormula(dates[colIndex] + concepts[rowIndex]);
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
