import Image from "next/image";
import Spreadsheet from '@/app/components/Spreadsheet';
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
    <div>
    <div>
      <Spreadsheet dates={dates} concepts={concepts}/>
    </div>
    <div>
      <FormulaBuilder />
    </div>

    </div>
  )
}
