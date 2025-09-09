import { storeFormula } from "@/app/utils/postgresUtils";
import { useRouter } from "next/navigation";

export default function FindStocksButton({ formula }: { formula: string }) {
  const router = useRouter();

  return (
    <div className="flex-1">
      <button
        className="mt-6 px-3 py-1 bg-lime-700 border border-lime-500 rounded text-3xl hover:bg-lime-900 cursor-pointer text-lime-50 hover:font-semibold"
        onClick={async () => {
          // TODO: check formula
          const [{ id }] = await storeFormula(formula);
          router.push(`/results?id=${id}`);
        }}
      >
        Find Stocks &#129122;
      </button>
    </div>
  );
}
