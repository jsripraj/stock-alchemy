"use server";

import postgres from "postgres";
import { getSqlQuery } from "@/app/utils/formulaUtils";

const sql = postgres(process.env.POSTGRES_URL!, { ssl: "require" });

export async function fetchResults(formula: string, dates: string[]) {
  const query = getSqlQuery(formula, dates[0]);

  if (query) {
    console.log(query);
    const data = await sql.unsafe(query);
    console.log(data);
  }
}
