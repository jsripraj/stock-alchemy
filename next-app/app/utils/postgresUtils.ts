"use server";

import postgres from "postgres";
import { getSqlQuery } from "@/app/utils/formulaUtils";

const sql = postgres(process.env.POSTGRES_URL!, { ssl: "require" });

export async function fetchResults(formula: string, mostRecentYear: string) {
  const query = getSqlQuery(formula, mostRecentYear);

  if (query) {
    const data = await sql.unsafe(query);
    return data;
  }
}
