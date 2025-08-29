import Image from "next/image";
import Spreadsheet from "@/app/components/Spreadsheet";
import FormulaBuilder from "./components/FormulaBuilder";

const dates = [
  "6/30/2025",
  "3/31/2025",
  "12/31/2024",
  "9/30/2024",
  "6/30/2024",
  "3/31/2024",
  "12/31/2023",
  "9/30/2023",
  "6/30/2023",
  "3/31/2023",
  "12/31/2022",
  "9/30/2022",
  "6/30/2022",
  "3/31/2022",
  "12/31/2021",
];

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
  return (
    <div className="w-screen h-screen">
      <h1 className="text-center text-4xl m-6">StockAlchemy</h1>
      <div className="m-4">
        <Spreadsheet dates={dates} concepts={concepts} />
      </div>
      <div className="m-4">
        <FormulaBuilder />
      </div>
    </div>
  );
}
