"use server";

import postgres from "postgres";
import { getSqlQuery } from "@/app/utils/formulaUtils";

const sql = postgres(process.env.POSTGRES_URL!, { ssl: "require" });

export async function fetchResults(formula: string, mostRecentYear: string, limit: number = -1) {
  const clean = formula.replace(/\u00A0/g, " ");
  const query = getSqlQuery(clean, mostRecentYear, limit);
  console.log(query);

  if (query) {
    const data = await sql.unsafe(query);
    return data;
  }
}

export async function storeFormula(formula: string) {
  const id = await sql`
    insert into formulas (formula)
    values (${formula})  
    returning id
  `;
  return id;
}

export async function fetchFormula(formulaId: string) {
  const formula = await sql`
    select formula
    from formulas
    where id = ${formulaId}
  `;
  return formula;
}
