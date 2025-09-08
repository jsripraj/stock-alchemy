"use client";

import { useState } from "react";
import Spreadsheet from "@/app/components/Spreadsheet";
import FormulaBuilder from "@/app/components/FormulaBuilder";
import FindStocksButton from "@/app/components/FindStocksButton";
import { getMostRecentYear } from "@/app/utils/formulaUtils";

const lastYear = getMostRecentYear();
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
    <div className="w-screen h-screen flex flex-col items-center overflow-hidden">
      <h1 className="text-center text-4xl m-6">StockAlchemy</h1>
      <div className="flex-1 w-8/10 flex flex-col items-center overflow-hidden">
        <Spreadsheet
          dates={dates}
          concepts={concepts}
          setFormula={setFormula}
        />
        <FormulaBuilder formula={formula} setFormula={setFormula} />
        <FindStocksButton formula={formula} />
      </div>
    </div>
  );
}
