"""Hybrid Categorization Engine Orchestrator.

Ref: PRD-SOL-01, ARCH-FLOW-01
Combines Tier-1 Heuristics and Tier-2 LLM Batching into a single,
production-grade classification pipeline.
"""

from typing import Dict, Tuple
import pandas as pd
from src.schemas import CleanedExpenseSchema, CategorizedExpenseSchema
from src.rules_engine import match_heuristic
from src.llm_categorizer import categorize_batch_with_llm


def categorize_expenses(
    df_cleaned: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Categorize expense dataframe using Hybrid Architecture.

    Ref: PRD-SOL-01
    Returns:
        (categorized_dataframe, metrics_summary)
    """
    # 1. Enforce input contract
    CleanedExpenseSchema.validate(df_cleaned)

    result_df = df_cleaned.copy().reset_index(drop=True)
    categories = [None] * len(result_df)
    sources = [None] * len(result_df)

    # 2. Tier-1: Heuristics Matching (<1ms)
    pending_indices = []
    pending_descriptions = []

    for idx in range(len(result_df)):
        desc = result_df.at[idx, "Clean_Description"]
        cat, src = match_heuristic(desc)
        if cat:
            categories[idx] = cat
            sources[idx] = src
        else:
            pending_indices.append(idx)
            pending_descriptions.append(desc)

    # 3. Tier-2: Gemini LLM Batching for unclassified transactions
    if pending_descriptions:
        llm_categories = categorize_batch_with_llm(pending_descriptions)
        for idx, cat in zip(pending_indices, llm_categories):
            categories[idx] = cat
            sources[idx] = "Gemini_AI"

    # Fill any remaining None with fallback
    for i in range(len(categories)):
        if categories[i] is None:
            categories[i] = "Lainnya"
            sources[i] = "Fallback"

    result_df["Category"] = categories
    result_df["Source"] = sources

    # 4. Enforce output contract
    validated_df = CategorizedExpenseSchema.validate(result_df)

    # 5. Compute efficiency metrics
    total = len(validated_df)
    heuristic_count = sum(1 for s in sources if s == "Heuristic_Rules")
    llm_count = sum(1 for s in sources if s == "Gemini_AI")

    metrics = {
        "total_transactions": total,
        "heuristic_count": heuristic_count,
        "heuristic_percentage": round((heuristic_count / total * 100), 1) if total else 0.0,
        "llm_count": llm_count,
        "llm_percentage": round((llm_count / total * 100), 1) if total else 0.0,
    }

    return validated_df, metrics
