'use server'

import postgres from "postgres";

const sql = postgres(process.env.POSTGRES_URL!, { ssl: "require" });

export async function fetchConcepts() {
  const data = await sql`
        select * from companies;
    `;
console.log('hello');
//   console.log(data);
}
