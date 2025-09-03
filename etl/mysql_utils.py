from dotenv import load_dotenv
import os
import config
from supabase import create_client, Client

load_dotenv()

def insert(table: str, data: list[dict]):
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    try:
        response = (
            supabase.table(table)
            .insert(data)
            .execute()
        )
        return response
    except Exception as exception:
        return exception