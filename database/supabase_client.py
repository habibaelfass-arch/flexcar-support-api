import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_instance: Client | None = None


def get_supabase_client() -> Client:
    global _supabase_instance
    if _supabase_instance is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        _supabase_instance = create_client(url, key)
    return _supabase_instance
