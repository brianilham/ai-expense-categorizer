"""Test Suite for Data Contracts & Preprocessing Pipeline.

Ref: PRD-METRIC-01, ARCH-SCHEMA-01
Test-Driven Data Science (TDDS) verification with pytest.
"""

import pytest
import pandas as pd
import pandera.errors
from src.schemas import RawTransactionSchema, CleanedExpenseSchema
from src.preprocessing import clean_and_filter_expenses


def test_raw_schema_valid():
    """Verify that correctly formatted raw banking data passes validation."""
    data = pd.DataFrame({
        "Date": ["2026-08-01", "2026-08-02"],
        "Amount": [100000.0, 25000.0],
        "Type": ["Debit", "Credit"],
        "Raw_Description": ["QRIS KOPI HOJA", "PAYROLL PT MAJU BERSAMA"],
    })
    validated = RawTransactionSchema.validate(data)
    assert len(validated) == 2


def test_raw_schema_rejects_negative_amount():
    """Verify that negative amounts fail fast at ingestion stage."""
    data = pd.DataFrame({
        "Date": ["2026-08-01"],
        "Amount": [-50000.0],
        "Type": ["Debit"],
        "Raw_Description": ["INVALID NEGATIVE AMOUNT"],
    })
    with pytest.raises(pandera.errors.SchemaError):
        RawTransactionSchema.validate(data)


def test_raw_schema_rejects_invalid_type():
    """Verify that unknown transaction types are rejected."""
    data = pd.DataFrame({
        "Date": ["2026-08-01"],
        "Amount": [50000.0],
        "Type": ["UnknownType"],
        "Raw_Description": ["UNKNOWN MUTATION TYPE"],
    })
    with pytest.raises(pandera.errors.SchemaError):
        RawTransactionSchema.validate(data)


def test_clean_and_filter_expenses():
    """Verify filtering of debit-only expenses and noise cleaning."""
    raw_data = pd.DataFrame({
        "Date": ["2026-08-01", "2026-08-02", "2026-08-03"],
        "Amount": ["10000000", "25000", "150000"],
        "Type": ["Credit", "Debit", "Debit"],
        "Raw_Description": [
            "PAYROLL PT MAJU BERSAMA",
            "  QRIS KOPI HOJA #123  ",
            "PAYMENT PLN TOKEN",
        ],
    })

    cleaned_df = clean_and_filter_expenses(raw_data)

    # 1. Credit transactions must be excluded
    assert len(cleaned_df) == 2
    assert "Credit" not in cleaned_df.get("Type", [])

    # 2. Amount must be positive numeric
    assert cleaned_df["Amount"].iloc[0] == 25000.0
    assert cleaned_df["Amount"].iloc[1] == 150000.0

    # 3. Clean_Description must be stripped of leading/trailing spaces
    assert cleaned_df["Clean_Description"].iloc[0] == "QRIS KOPI HOJA"

    # 4. Validated against CleanedExpenseSchema
    CleanedExpenseSchema.validate(cleaned_df)
