"use client";

import { useState } from "react";
import Spreadsheet from "@/app/components/Spreadsheet";
import FormulaBuilder from "./components/FormulaBuilder";


const lastYear = new Date().getFullYear() - 1;
const dates = [...Array(10)].map((_, i) => (lastYear - i).toString());

const concepts = [
  "Shares Outstanding",
  "Cash and Cash Equivalents",
  "Assets",
  "Short-Term Debt",
  "Long-Term Debt",
  "Equity",
  "Revenue",
  "Net Income",
  "Cash Flow from Operating Activities",
  "Cash Flow from Investing Activities",
  "Cash Flow from Financing Activities",
  "Capital Expenditures",
  "Dividends",
];

export default function Home() {
  const [formula, setFormula] = useState("");

  return (
    <div className="w-screen h-screen flex flex-col">
      <h1 className="text-center text-4xl p-6">StockAlchemy</h1>
      <div className="flex-1 m-4 overflow-auto">
        <Spreadsheet
          dates={dates}
          concepts={concepts}
          setFormula={setFormula}
        />
      </div>
      <div className="flex-1 p-4 overflow-auto">
        <FormulaBuilder formula={formula} setFormula={setFormula} />
      </div>
    </div>
  );
}
