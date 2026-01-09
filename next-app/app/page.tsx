"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Spreadsheet from "@/app/components/page/Spreadsheet";
import FormulaBuilder from "@/app/components/page/FormulaBuilder";
import FindStocksButton from "@/app/components/page/FindStocksButton";
import { getMostRecentYear, isValidFormula } from "@/app/utils/formulaUtils";
import { storeFormula } from "@/app/utils/postgresUtils";

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
  const [formula, setFormula] = useState(typeof window !== "undefined" ? (sessionStorage?.getItem("formula") || "") : "");
  const [errorMessage, setErrorMessage] = useState("");
  const [isMessageVisable, setIsMessageVisable] = useState(false);
  const cursorPosRef = useRef<number>(0);
  const timerID = useRef<NodeJS.Timeout>(null);
  const router = useRouter();

  useEffect(() => {
    sessionStorage?.setItem("formula", formula);
  }, [formula]);

  function insertIntoFormula(insertIndex: number, str: string) {
    setFormula((f) => {
      const left = f.substring(0, insertIndex);
      const right = f.substring(insertIndex);
      return left + str + right;
    });
  }

  async function findStocksClicked() {
    const { result, message } = await isValidFormula(formula, dates, concepts);
    if (!result) {
      setErrorMessage(message);
      startMessageTimer();
    } else {
      const [{ id }] = await storeFormula(formula); // normalize to prevent hidden whitespace chars?
      router.push(`/results?id=${id}`);
    }
  }

  function startMessageTimer() {
    setIsMessageVisable(true);
    if (timerID.current) {
      clearTimeout(timerID.current);
    }
    timerID.current = setTimeout(() => {
      setIsMessageVisable(false);
    }, 10000);
  }

  return (
    <div className="flex-1 w-8/10 flex flex-col items-center overflow-hidden">
      <Spreadsheet
        dates={dates}
        concepts={concepts}
        cursorPosRef={cursorPosRef}
        insertIntoFormula={insertIntoFormula}
      />
      <FormulaBuilder
        formula={formula}
        insertIntoFormula={insertIntoFormula}
        setFormula={setFormula}
        cursorPosRef={cursorPosRef}
        dates={dates}
        concepts={concepts}
        errorMessage={errorMessage}
        isMessageVisable={isMessageVisable}
      />
      <FindStocksButton
        findStocksClicked={findStocksClicked}
      />
    </div>
  );
}
