import { fetchResults, fetchFormula } from "@/app/utils/postgresUtils";

interface ResultsPageProps {
    searchParams: { id?: string };
}

export default async function ResultsPage({ searchParams }: ResultsPageProps) {
  const sp = await searchParams;
  const formulaId = sp.id;
  if (formulaId) {
    const [{ formula }] = await fetchFormula(formulaId);
    console.log(formula);
  }
  return <p>Results Page</p>;
}
