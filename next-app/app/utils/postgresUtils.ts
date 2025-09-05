"use server";

import postgres from "postgres";
import { extractTokens } from "@/app/utils/formulaUtils";

const sql = postgres(process.env.POSTGRES_URL!, { ssl: "require" });

export async function fetchResults(formula: string) {
  const tokens = extractTokens(formula);
  console.log(...tokens);
  const data = await sql`
        select * from companies;
    `;
  // console.log("hello");
  //   console.log(data);
}
