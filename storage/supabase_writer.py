import os
from typing import Any, Mapping
from utils.logger import setup_logging
from pathlib import Path

LOGGER = setup_logging(Path(__file__).parent.parent / "output" / "logs")

try:
    from supabase import create_client, Client
except ImportError:
    Client = None
    create_client = None

def get_supabase_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if url and key and create_client:
        return create_client(url, key)
    return None

def upsert_job(job: dict[str, Any] | list[dict[str, Any]]) -> None:
    client = get_supabase_client()
    if not client or not job:
        return
    try:
        client.table("jobs").upsert(job).execute()
    except Exception as e:
        LOGGER.error(f"Supabase upsert_job error: {e}")

def get_all_jobs() -> list[dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return []
    try:
        res = client.table("jobs").select("*").order("startTime", desc=True).execute()
        return res.data
    except Exception as e:
        LOGGER.error(f"Supabase get_all_jobs error: {e}")
        return []

def clear_all_jobs() -> None:
    client = get_supabase_client()
    if not client:
        return
    try:
        # Supabase doesn't easily support DELETE without conditions directly using the builder in python simply, 
        # so we delete where ID is not null (which matches everything)
        client.table("jobs").delete().neq('id', 'dummy_value_that_doesnt_exist').execute()
    except Exception as e:
        LOGGER.error(f"Supabase clear_all_jobs error: {e}")

def upsert_companies(records: list[dict[str, Any]]) -> None:
    client = get_supabase_client()
    if not client or not records:
        return
    try:
        # Supabase bulk upsert
        client.table("companies").upsert(records).execute()
    except Exception as e:
        LOGGER.error(f"Supabase upsert_companies error: {e}")

def get_all_companies() -> list[dict[str, Any]]:
    client = get_supabase_client()
    if not client:
        return []
    try:
        res = client.table("companies").select("*").execute()
        return res.data
    except Exception as e:
        LOGGER.error(f"Supabase get_all_companies error: {e}")
        return []
