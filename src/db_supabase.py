"""Supabase PostgreSQL Cloud Synchronization Module.

Ref: ARCH-TECH-01, PRD-DATA-01
Uploads categorized expense data to Supabase using Session Pooler (port 5432).
"""

import os
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
import pandas as pd
from sqlalchemy import create_engine, text

load_dotenv(override=True)


def get_supabase_engine():
    """Create SQLAlchemy engine using credentials from .env."""
    user = os.getenv("user")
    password = os.getenv("password")
    host = os.getenv("host")
    port = os.getenv("port", "5432")
    dbname = os.getenv("dbname", "postgres")

    if not all([user, password, host]):
        # Fallback to SUPABASE_DB_URL if defined
        db_url = os.getenv("SUPABASE_DB_URL")
        if not db_url:
            raise ValueError(
                "Kredensial database Supabase tidak lengkap di file .env!"
            )
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
        return create_engine(db_url)

    # Sanitize password from any accidental brackets
    clean_password = password.strip("[]")

    db_url = (
        f"postgresql+psycopg2://{user}:{clean_password}@{host}:{port}/{dbname}?sslmode=require"
    )
    return create_engine(db_url)


def test_supabase_connection() -> Tuple[bool, str]:
    """Test connection to Supabase database."""
    try:
        engine = get_supabase_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Koneksi ke Supabase berhasil!"
    except Exception as e:
        return False, f"Gagal terhubung ke Supabase: {e}"


def upload_expenses_to_supabase(
    df: pd.DataFrame, table_name: str = "expenses", if_exists: str = "replace"
) -> Dict[str, Any]:
    """Upload categorized expenses to Supabase PostgreSQL table."""
    try:
        engine = get_supabase_engine()
        # Ensure Date is written as date/string, not timestamp with tz issue
        df_upload = df.copy()
        if "Date" in df_upload.columns:
            df_upload["Date"] = pd.to_datetime(df_upload["Date"]).dt.strftime("%Y-%m-%d")

        df_upload.to_sql(table_name, engine, if_exists=if_exists, index=False)
        return {
            "success": True,
            "rows_uploaded": len(df_upload),
            "table_name": table_name,
            "message": f"Berhasil menyimpan {len(df_upload)} baris data ke Supabase!",
        }
    except Exception as e:
        return {
            "success": False,
            "rows_uploaded": 0,
            "table_name": table_name,
            "message": f"Terjadi kesalahan saat upload ke Supabase: {e}",
        }
