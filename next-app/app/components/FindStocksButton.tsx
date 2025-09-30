import { storeFormula } from "@/app/utils/postgresUtils";
import { isValidFormula } from "@/app/utils/formulaUtils";
import { useRouter } from "next/navigation";
import { SetStateAction } from "react";

export default function FindStocksButton({
  formula,
  dates,
  concepts,
  setErrorMessage,
  startMessageTimer,
}: {
  formula: string;
  dates: string[];
  concepts: string[];
  setErrorMessage: React.Dispatch<SetStateAction<string>>;
  startMessageTimer: () => void;
}) {
  const router = useRouter();

  return (
    <div className="flex-1 flex flex-col items-center">
      <button
        className="m-3 p-3 bg-lime-700 border border-lime-500 rounded text-3xl hover:bg-lime-900 cursor-pointer text-lime-50 hover:font-semibold"
        onClick={async () => {
          const { result, message } = isValidFormula(formula, dates, concepts);
          console.log(`result: ${result}`);
          console.log(`message: ${message}`);
          if (!result) {
            setErrorMessage(message);
            startMessageTimer();
          } else {
            const [{ id }] = await storeFormula(formula); // normalize to prevent hidden whitespace chars?
            router.push(`/results?id=${id}`);
          }
        }}
      >
        Find Stocks &#129122;
      </button>
    </div>
  );
}
