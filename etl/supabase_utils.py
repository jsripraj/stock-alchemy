from dotenv import load_dotenv
import os
import config
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def batchInsert(tablename: str, rows: list[dict], logger, batchSize: int = config.BATCH_SIZE_SUPABASE):
    for i in range(0, len(rows), batchSize):
        batch = rows[i:i + batchSize]
        try:
            response = supabase.table(tablename).insert(batch).execute()
        except Exception as e:
            logger.error(f"Error inserting into {tablename} table: {e}")


def batchFetch(tablename: str, columns: list[str], logger, batchSize: int = config.BATCH_SIZE_SUPABASE):
    start = 0
    rows = []
    while True:
        try:
            end = start + batchSize - 1
            response = (
                supabase.table(tablename)
                .select(", ".join(columns))
                .range(start, end)
                .execute()
            )
        except Exception as e:
            logger.error(f"Error fetching from {tablename} table: {e}")
            break
        if not response.data:
            break
        rows.extend(response.data)
        start += batchSize
    return rows


def truncate(table: str):
    try:
        response = supabase.rpc("truncate_table", {"tablename": table}).execute()
        return response
    except Exception:
        raise