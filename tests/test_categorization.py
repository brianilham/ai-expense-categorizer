"""Test Suite for Rules Engine & Categorization Pipeline."""

import pandas as pd
from src.rules_engine import match_heuristic
from src.categorizer import categorize_expenses


def test_heuristic_rules_matching():
    """Verify common Indonesian merchants are caught by Tier-1 Heuristics."""
    cat, src = match_heuristic("PAYMENT PLN TOKEN")
    assert cat == "Utilitas"
    assert src == "Heuristic_Rules"

    cat, src = match_heuristic("SPOTIFY PREMIUM")
    assert cat == "Hiburan"
    assert src == "Heuristic_Rules"

    cat, src = match_heuristic("WD ATM MANDIRI")
    assert cat == "Transfer/Tarik Tunai"
    assert src == "Heuristic_Rules"

    cat, src = match_heuristic("ORANGE CARWASH")
    assert cat == "Perawatan Kendaraan"
    assert src == "Heuristic_Rules"

    cat, src = match_heuristic("SUPERINDO FRESH MARKET")
    assert cat == "Kebutuhan Rumah Tangga"
    assert src == "Heuristic_Rules"

    cat, src = match_heuristic("UNKNOWN LOCAL MERCHANT")
    assert cat is None
    assert src is None


def test_categorize_expenses_pipeline():
    """Verify end-to-end categorization produces valid schema."""
    df_clean = pd.DataFrame({
        "Date": ["2026-08-01", "2026-08-02"],
        "Amount": [150000.0, 54900.0],
        "Raw_Description": ["PAYMENT PLN TOKEN", "SPOTIFY PREMIUM"],
        "Clean_Description": ["PAYMENT PLN TOKEN", "SPOTIFY PREMIUM"],
    })

    result_df, metrics = categorize_expenses(df_clean)

    assert len(result_df) == 2
    assert "Category" in result_df.columns
    assert "Source" in result_df.columns
    assert metrics["heuristic_count"] == 2
    assert metrics["heuristic_percentage"] == 100.0
