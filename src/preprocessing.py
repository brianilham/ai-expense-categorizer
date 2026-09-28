"""Data Preprocessing & Cleaning Pipeline.

Ref: PRD-REQ-01, ARCH-FLOW-01
Filters debit expenses, validates schemas, and normalizes merchant text.
"""

import re
import pandas as pd
from src.schemas import RawTransactionSchema, CleanedExpenseSchema


def clean_description(text: str) -> str:
    """Normalize raw transaction description.

    Removes transaction noise, reference hashtags (#123), and excessive spaces.
    """
    if not isinstance(text, str):
        return ""
    # Strip whitespace
    cleaned = text.strip()
    # Remove trailing hashtag codes: #123, #456
    cleaned = re.sub(r"\s*#\d+\b", "", cleaned)
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def clean_and_filter_expenses(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess and filter debit-only expenses.

    Ref: PRD-REQ-01
    """
    # 1. Enforce Raw Data Contract
    validated_raw = RawTransactionSchema.validate(df)

    # 2. Filter Debit (Expense) Only
    is_debit = validated_raw["Type"].astype(str).str.strip().str.lower() == "debit"
    df_expenses = validated_raw[is_debit].copy()

    # 3. Format Date
    df_expenses["Date"] = pd.to_datetime(df_expenses["Date"]).dt.strftime("%Y-%m-%d")

    # 4. Clean and Normalize Description
    df_expenses["Raw_Description"] = df_expenses["Raw_Description"].astype(str).str.strip()
    df_expenses["Clean_Description"] = df_expenses["Raw_Description"].apply(clean_description)

    # 5. Drop Type and reset index
    if "Type" in df_expenses.columns:
        df_expenses = df_expenses.drop(columns=["Type"])
    df_expenses = df_expenses.reset_index(drop=True)

    # 6. Validate Cleaned Schema
    return CleanedExpenseSchema.validate(df_expenses)
