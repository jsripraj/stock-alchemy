"use server";

import postgres from "postgres";
import { extractTokens, getSqlSelectTerm} from "@/app/utils/formulaUtils";

const sql = postgres(process.env.POSTGRES_URL!, { ssl: "require" });

export async function fetchResults(formula: string, dates: string[]) {
  const tokens = extractTokens(formula);

  const test = getSqlSelectTerm("[2024 Net Income]", dates[0]);
  console.log(test);

  const data = await sql`
        select * from companies;
    `;
  // console.log("hello");
  //   console.log(data);
}
