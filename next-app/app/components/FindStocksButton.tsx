import { storeFormula } from "@/app/utils/postgresUtils";
import { useRouter } from "next/navigation";

export default function FindStocksButton({ formula }: { formula: string }) {
  const router = useRouter();

  return (
    <div className="flex-1">
      <button
        className="px-3 py-1 bg-green-200 rounded text-2xl hover:bg-green-300 cursor-pointer"
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
