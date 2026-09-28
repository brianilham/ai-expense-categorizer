"""DuckDB In-Memory OLAP Engine.

Ref: ARCH-TECH-01, PRD-SLA-01
Ultra-fast sub-millisecond local analytical query engine for Streamlit dashboard.
"""

from typing import Dict, Any, Optional
import duckdb
import pandas as pd


def get_duckdb_connection(db_file: str = ":memory:") -> duckdb.DuckDBPyConnection:
    """Create or retrieve a DuckDB database connection."""
    return duckdb.connect(database=db_file)


def load_dataframe_to_duckdb(
    df: pd.DataFrame,
    table_name: str = "expenses",
    conn: Optional[duckdb.DuckDBPyConnection] = None,
) -> duckdb.DuckDBPyConnection:
    """Load categorized DataFrame into DuckDB table."""
    if conn is None:
        conn = get_duckdb_connection()

    conn.register("df_temp", df)
    conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_temp")
    conn.unregister("df_temp")
    return conn


def get_category_breakdown(
    conn: duckdb.DuckDBPyConnection, table_name: str = "expenses"
) -> pd.DataFrame:
    """Calculate aggregated expenses per category with sub-millisecond execution.

    Ref: PRD-SLA-01
    """
    query = f"""
    SELECT 
        Category,
        CAST(SUM(Amount) AS DOUBLE) AS Total_Amount,
        COUNT(*) AS Transaction_Count,
        ROUND(CAST(SUM(Amount) AS DOUBLE) * 100.0 / SUM(SUM(Amount)) OVER (), 1) AS Percentage
    FROM {table_name}
    GROUP BY Category
    ORDER BY Total_Amount DESC
    """
    return conn.execute(query).df()


def get_daily_trend(
    conn: duckdb.DuckDBPyConnection, table_name: str = "expenses"
) -> pd.DataFrame:
    """Calculate daily expenditure trend."""
    query = f"""
    SELECT 
        Date,
        CAST(SUM(Amount) AS DOUBLE) AS Daily_Total,
        COUNT(*) AS Transaction_Count
    FROM {table_name}
    GROUP BY Date
    ORDER BY Date ASC
    """
    return conn.execute(query).df()


def get_kpi_summary(
    conn: duckdb.DuckDBPyConnection, table_name: str = "expenses"
) -> Dict[str, Any]:
    """Calculate executive KPI numbers for dashboard display."""
    query = f"""
    SELECT 
        COALESCE(SUM(Amount), 0) AS total_expense,
        COUNT(*) AS total_transactions,
        COALESCE(AVG(Amount), 0) AS avg_transaction,
        COUNT(DISTINCT Category) AS distinct_categories,
        SUM(CASE WHEN Source = 'Heuristic_Rules' THEN 1 ELSE 0 END) AS heuristic_count,
        SUM(CASE WHEN Source = 'Gemini_AI' THEN 1 ELSE 0 END) AS llm_count
    FROM {table_name}
    """
    row = conn.execute(query).fetchone()
    total_tx = row[1] or 0
    heur_cnt = row[4] or 0
    llm_cnt = row[5] or 0

    return {
        "total_expense": float(row[0] or 0),
        "total_transactions": int(total_tx),
        "avg_transaction": float(row[2] or 0),
        "distinct_categories": int(row[3] or 0),
        "heuristic_count": int(heur_cnt),
        "heuristic_percentage": round(heur_cnt / total_tx * 100, 1) if total_tx else 0.0,
        "llm_count": int(llm_cnt),
        "llm_percentage": round(llm_cnt / total_tx * 100, 1) if total_tx else 0.0,
    }
