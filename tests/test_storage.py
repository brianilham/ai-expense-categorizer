"""Test Suite for DuckDB Analytics & Storage Layer."""

import pandas as pd
from src.db_duckdb import (
    get_duckdb_connection,
    load_dataframe_to_duckdb,
    get_category_breakdown,
    get_kpi_summary,
)


def test_duckdb_aggregations():
    """Verify DuckDB accurately calculates breakdown and KPIs."""
    df = pd.DataFrame({
        "Date": ["2026-08-01", "2026-08-01", "2026-08-02"],
        "Amount": [100000.0, 50000.0, 50000.0],
        "Raw_Description": ["PLN", "PULSA", "WARTEG"],
        "Clean_Description": ["PLN", "PULSA", "WARTEG"],
        "Category": ["Utilitas", "Utilitas", "F&B"],
        "Source": ["Heuristic_Rules", "Heuristic_Rules", "Gemini_AI"],
    })

    conn = get_duckdb_connection()
    load_dataframe_to_duckdb(df, "test_expenses", conn)

    breakdown = get_category_breakdown(conn, "test_expenses")
    assert len(breakdown) == 2
    # Utilitas total should be 150000
    utilitas_row = breakdown[breakdown["Category"] == "Utilitas"].iloc[0]
    assert utilitas_row["Total_Amount"] == 150000.0
    assert utilitas_row["Percentage"] == 75.0

    kpis = get_kpi_summary(conn, "test_expenses")
    assert kpis["total_expense"] == 200000.0
    assert kpis["total_transactions"] == 3
    assert kpis["heuristic_count"] == 2
    assert kpis["heuristic_percentage"] == 66.7
