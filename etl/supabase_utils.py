from dotenv import load_dotenv
import os
import config
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def insert(table: str, rows: list[dict]):
    try:
        response = supabase.table(table).insert(rows).execute()
        return response
    except Exception as exception:
        return exception


def fetch(table: str, columns: list[str]):
    limit = config.SUPABASE_MAX_ROWS
    start, end = 0, limit - 1
    rows = []
    while True:
        try:
            response = (
                supabase.table(table)
                .select(", ".join(columns))
                .range(start, end)
                .execute()
            )
        except Exception as exception:
            return exception
        if not response.data:
            return rows
        rows += response.data
        start, end = start + limit, end + limit
