"""Enterprise Expense Intelligence & Categorization Platform.

Ref: PRD-REQ-01, PRD-SOL-01, ARCH-TECH-01, streamlit-taste (Anti-Slop Corporate Edition)
Streamlit analytical dashboard powered by Hybrid Heuristics + Gemini LLM and DuckDB OLAP.
"""

from typing import Dict, Any, Tuple
import os
import io
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from src.schemas import RawTransactionSchema, CleanedExpenseSchema, CategorizedExpenseSchema
from src.preprocessing import clean_and_filter_expenses
from src.categorizer import categorize_expenses
from src.data_generator import generate_synthetic_transactions
from src.db_duckdb import (
    load_dataframe_to_duckdb,
    get_category_breakdown,
    get_daily_trend,
    get_kpi_summary,
    get_duckdb_connection,
)
from src.db_supabase import upload_expenses_to_supabase, test_supabase_connection

# -----------------------------------------------------------------------------
# Configuration & Theme Tokens
# -----------------------------------------------------------------------------
BRAND_COLOR = "#0284c7"  # Corporate Blue
BG_CANVAS = "#09090b"
BG_CARD = "#111418"
BORDER_COLOR = "rgba(255, 255, 255, 0.10)"
BORDER_HOVER = "rgba(255, 255, 255, 0.20)"
TEXT_PRIMARY = "#f8fafc"
TEXT_SECONDARY = "#cbd5e1"
TEXT_MUTED = "#94a3b8"

st.set_page_config(
    page_title="Expense Intelligence Platform",
    page_icon="none",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_custom_styles() -> None:
    """Inject corporate typography, micro-borders, and high-legibility CSS."""
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            font-size: 16px !important;
            line-height: 1.6 !important;
            color: {TEXT_PRIMARY} !important;
        }}
        
        h1 {{
            font-size: 2.2rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.03em !important;
            color: {TEXT_PRIMARY} !important;
            margin-bottom: 0.25rem !important;
            padding-bottom: 0 !important;
        }}
        
        h2 {{
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            letter-spacing: -0.02em !important;
            color: {TEXT_PRIMARY} !important;
        }}
        
        h3 {{
            font-size: 1.2rem !important;
            font-weight: 600 !important;
            color: {TEXT_SECONDARY} !important;
        }}
        
        div[data-testid="stMetric"],
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stExpander"] {{
            background-color: {BG_CARD} !important;
            border: 1px solid {BORDER_COLOR} !important;
            border-radius: 12px !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }}
        
        div[data-testid="stMetric"]:hover,
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            border-color: {BORDER_HOVER} !important;
        }}
        
        div[data-testid="stMetricValue"] {{
            font-size: 2.25rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.03em !important;
            color: {TEXT_PRIMARY} !important;
            line-height: 1.2 !important;
        }}
        
        div[data-testid="stMetricLabel"] {{
            font-size: 0.92rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            color: {TEXT_SECONDARY} !important;
        }}
        
        button[data-baseweb="tab"] {{
            font-size: 1.0rem !important;
            font-weight: 500 !important;
            padding: 10px 18px !important;
            color: {TEXT_MUTED} !important;
        }}
        
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {BRAND_COLOR} !important;
            font-weight: 600 !important;
            border-bottom-color: {BRAND_COLOR} !important;
        }}
        
        div[data-testid="stDataFrame"] {{
            border-radius: 10px !important;
            border: 1px solid {BORDER_COLOR} !important;
        }}
        
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Cached Analytical & Pipeline Operations
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_benchmark_dataset() -> pd.DataFrame:
    """Generate or retrieve standard benchmark dataset."""
    csv_path = "synthetic_transactions.csv"
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    df = generate_synthetic_transactions(160)
    df.to_csv(csv_path, index=False)
    return df


@st.cache_data(show_spinner=False)
def process_pipeline(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Execute end-to-end cleaning and hybrid categorization pipeline."""
    cleaned_df = clean_and_filter_expenses(raw_df)
    categorized_df, metrics = categorize_expenses(cleaned_df)
    return categorized_df, metrics


@st.cache_data(show_spinner=False)
def compute_duckdb_metrics(df_json: str) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """Execute analytical queries on in-memory DuckDB engine with sub-millisecond latency."""
    df = pd.read_json(io.StringIO(df_json), orient="split")
    conn = get_duckdb_connection()
    load_dataframe_to_duckdb(df, table_name="expenses", conn=conn)

    kpi = get_kpi_summary(conn, "expenses")
    breakdown = get_category_breakdown(conn, "expenses")
    trend = get_daily_trend(conn, "expenses")
    return kpi, breakdown, trend


# -----------------------------------------------------------------------------
# Chart Builders (Plotly Zero Chart-Junk)
# -----------------------------------------------------------------------------
def build_category_bar_chart(breakdown_df: pd.DataFrame) -> go.Figure:
    """Build corporate horizontal bar chart sorted descending by total expenditure."""
    df_sorted = breakdown_df.sort_values(by="Total_Amount", ascending=True)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df_sorted["Category"],
            x=df_sorted["Total_Amount"],
            orientation="h",
            marker=dict(
                color=BRAND_COLOR,
                line=dict(color="rgba(255, 255, 255, 0.15)", width=1),
            ),
            customdata=df_sorted[["Percentage", "Transaction_Count"]],
            hovertemplate="<b>%{y}</b><br>Total: Rp %{x:,.0f}<br>Share: %{customdata[0]:.1f}%<br>Count: %{customdata[1]} tx<extra></extra>",
        )
    )

    fig.update_layout(
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=20, t=10, b=10),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.06)",
            tickfont=dict(color=TEXT_MUTED, size=12),
            zeroline=False,
            title="",
        ),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_PRIMARY, size=13),
            title="",
        ),
        hoverlabel=dict(
            bgcolor=BG_CARD,
            font_size=13,
            font_family="Plus Jakarta Sans",
            bordercolor=BORDER_COLOR,
        ),
    )
    return fig


def build_trend_area_chart(trend_df: pd.DataFrame) -> go.Figure:
    """Build clean daily expenditure area trend chart."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trend_df["Date"],
            y=trend_df["Daily_Total"],
            mode="lines+markers",
            line=dict(color=BRAND_COLOR, width=2.5),
            marker=dict(size=5, color=BRAND_COLOR),
            fill="tozeroy",
            fillcolor="rgba(2, 132, 199, 0.12)",
            customdata=trend_df["Transaction_Count"],
            hovertemplate="<b>Date: %{x}</b><br>Spend: Rp %{y:,.0f}<br>Volume: %{customdata} tx<extra></extra>",
        )
    )

    fig.update_layout(
        height=360,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=20, t=15, b=10),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color=TEXT_MUTED, size=12),
            zeroline=False,
            title="",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255, 255, 255, 0.06)",
            tickfont=dict(color=TEXT_MUTED, size=12),
            zeroline=False,
            title="",
        ),
        hoverlabel=dict(
            bgcolor=BG_CARD,
            font_size=13,
            font_family="Plus Jakarta Sans",
            bordercolor=BORDER_COLOR,
        ),
    )
    return fig


# -----------------------------------------------------------------------------
# Main Application Flow
# -----------------------------------------------------------------------------
def main() -> None:
    inject_custom_styles()

    # Session State Initialization
    if "raw_df" not in st.session_state:
        st.session_state["raw_df"] = load_benchmark_dataset()
    if "categorized_df" not in st.session_state:
        categorized, metrics = process_pipeline(st.session_state["raw_df"])
        st.session_state["categorized_df"] = categorized
        st.session_state["pipeline_metrics"] = metrics

    # -------------------------------------------------------------------------
    # Sidebar: Data Ingestion & Control
    # -------------------------------------------------------------------------
    with st.sidebar:
        st.markdown("### Data Ingestion & Control")
        st.caption("Load statement transactions or ingest custom enterprise CSV.")

        uploaded_file = st.file_uploader(
            "Upload Bank Statement CSV",
            type=["csv"],
            help="CSV must adhere to RawTransactionSchema (Date, Raw_Description, Amount, Type)",
        )

        col_side1, col_side2 = st.columns(2)
        with col_side1:
            if st.button("Load Benchmark", use_container_width=True):
                st.session_state["raw_df"] = load_benchmark_dataset()
                categorized, metrics = process_pipeline(st.session_state["raw_df"])
                st.session_state["categorized_df"] = categorized
                st.session_state["pipeline_metrics"] = metrics
                st.rerun()

        with col_side2:
            if st.button("Generate New", use_container_width=True):
                new_df = generate_synthetic_transactions(160)
                st.session_state["raw_df"] = new_df
                categorized, metrics = process_pipeline(new_df)
                st.session_state["categorized_df"] = categorized
                st.session_state["pipeline_metrics"] = metrics
                st.rerun()

        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                st.session_state["raw_df"] = uploaded_df
                categorized, metrics = process_pipeline(uploaded_df)
                st.session_state["categorized_df"] = categorized
                st.session_state["pipeline_metrics"] = metrics
                st.success("Uploaded dataset validated and processed.")
            except Exception as err:
                st.error(f"Schema Contract Violation: {err}")

        st.markdown("---")
        st.markdown("### Pipeline Architecture")
        st.markdown(
            """
            - **Contract Validation**: Pandera Fail-Fast
            - **Tier-1 Engine**: Regex Heuristics (<1ms)
            - **Tier-2 Engine**: Gemini 3.5 Flash Lite
            - **Analytical Layer**: In-Memory DuckDB
            - **Cloud Storage**: Supabase PostgreSQL
            """
        )

        # Connection health check
        is_connected, msg = test_supabase_connection()
        if is_connected:
            st.caption("Supabase Cloud Pooler: Online (Port 5432)")
        else:
            st.caption(f"Supabase Cloud Pooler: Offline ({msg})")

    # -------------------------------------------------------------------------
    # Tier 1: Header Section
    # -------------------------------------------------------------------------
    st.markdown("# EXPENSE INTELLIGENCE PLATFORM")
    st.caption(
        "Production-Grade Hybrid Expense Classification Engine (Heuristics + Gemini LLM) with DuckDB Analytical Acceleration."
    )
    st.markdown("---")

    categorized_df: pd.DataFrame = st.session_state["categorized_df"]
    metrics: Dict[str, Any] = st.session_state.get("pipeline_metrics", {})

    # Compute DuckDB analytical metrics
    df_json = categorized_df.to_json(orient="split", date_format="iso")
    kpi, breakdown_df, trend_df = compute_duckdb_metrics(df_json)

    # -------------------------------------------------------------------------
    # Tier 2: Pulse Check (Executive KPI Cards)
    # -------------------------------------------------------------------------
    total_expense = kpi.get("total_expense", 0.0)
    total_tx = kpi.get("total_transactions", 0)
    heuristic_pct = kpi.get("heuristic_percentage", 0.0)
    llm_pct = kpi.get("llm_percentage", 0.0)

    # Format human-friendly IDR
    if total_expense >= 1_000_000_000:
        formatted_expense = f"Rp {total_expense / 1_000_000_000:.2f}B"
    elif total_expense >= 1_000_000:
        formatted_expense = f"Rp {total_expense / 1_000_000:.2f}M"
    else:
        formatted_expense = f"Rp {total_expense:,.0f}"

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric(label="TOTAL EXPENDITURE", value=formatted_expense, border=True)
    with kpi2:
        st.metric(label="TOTAL TRANSACTIONS", value=f"{total_tx:,}", border=True)
    with kpi3:
        st.metric(
            label="HEURISTIC COVERAGE",
            value=f"{heuristic_pct:.1f}%",
            delta=f"{kpi.get('heuristic_count', 0)} Zero-Cost Hits",
            border=True,
        )
    with kpi4:
        st.metric(
            label="LLM INFERENCE RATE",
            value=f"{llm_pct:.1f}%",
            delta=f"{kpi.get('llm_count', 0)} Batched Calls",
            delta_color="off",
            border=True,
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # Tier 3: Deep Dive (Tabbed Progressive Disclosure)
    # -------------------------------------------------------------------------
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Category Allocation",
            "Temporal Cash Flow",
            "Transaction Ledger",
            "Enterprise Governance",
        ]
    )

    # --- TAB 1: Category Allocation ---
    with tab1:
        st.markdown("### Expense Breakdown by Business Category")
        st.caption("Aggregated in real-time via in-memory DuckDB OLAP engine.")

        col_chart, col_table = st.columns([2.6, 1.4])

        with col_chart:
            bar_fig = build_category_bar_chart(breakdown_df)
            st.plotly_chart(bar_fig, use_container_width=True)

        with col_table:
            table_display = breakdown_df.copy()
            st.dataframe(
                table_display,
                column_config={
                    "Category": st.column_config.TextColumn("Category", width="medium"),
                    "Total_Amount": st.column_config.NumberColumn(
                        "Total (IDR)", format="Rp %,.0f", width="small"
                    ),
                    "Transaction_Count": st.column_config.NumberColumn("Volume", width="small"),
                    "Percentage": st.column_config.ProgressColumn(
                        "Share", format="%.1f%%", min_value=0.0, max_value=100.0, width="small"
                    ),
                },
                hide_index=True,
                use_container_width=True,
            )

    # --- TAB 2: Temporal Cash Flow ---
    with tab2:
        st.markdown("### Daily Expenditure Trajectory")
        st.caption("Chronological disbursement patterns across statement timeline.")

        trend_fig = build_trend_area_chart(trend_df)
        st.plotly_chart(trend_fig, use_container_width=True)

        st.markdown("### Tier Classification Attribution")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.info(
                f"**Tier-1 Heuristics Match**: {kpi.get('heuristic_count', 0)} transactions "
                f"({kpi.get('heuristic_percentage', 0.0)}%) resolved in under 1ms with $0 API expense."
            )
        with col_m2:
            st.info(
                f"**Tier-2 Gemini LLM Batch**: {kpi.get('llm_count', 0)} transactions "
                f"({kpi.get('llm_percentage', 0.0)}%) classified using Google Gemini 3.5 Flash Lite."
            )

    # --- TAB 3: Transaction Ledger & Cloud Sync ---
    with tab3:
        st.markdown("### Comprehensive Transaction Explorer")
        st.caption("Filter and inspect normalized debit transactions with engine metadata.")

        # Interactive filter controls
        all_categories = sorted(categorized_df["Category"].dropna().unique().tolist())
        filter_col1, filter_col2 = st.columns([3, 1])

        with filter_col1:
            selected_categories = st.multiselect(
                "Filter by Categories",
                options=all_categories,
                default=[],
                placeholder="All Categories (Select to filter)",
            )

        with filter_col2:
            selected_source = st.selectbox(
                "Engine Source",
                options=["All Sources", "Heuristic_Rules", "Gemini_AI"],
                index=0,
            )

        # Apply filtering
        filtered_df = categorized_df.copy()
        if selected_categories:
            filtered_df = filtered_df[filtered_df["Category"].isin(selected_categories)]
        if selected_source != "All Sources":
            filtered_df = filtered_df[filtered_df["Source"] == selected_source]

        if len(filtered_df) == 0:
            st.info("No transaction records match the specified filter criteria.")
        else:
            st.dataframe(
                filtered_df,
                column_config={
                    "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD", width="small"),
                    "Raw_Description": st.column_config.TextColumn(
                        "Raw Merchant Description", width="large"
                    ),
                    "Clean_Description": st.column_config.TextColumn("Normalized", width="medium"),
                    "Amount": st.column_config.NumberColumn(
                        "Amount (IDR)", format="Rp %,.0f", width="small"
                    ),
                    "Category": st.column_config.TextColumn("Category", width="medium"),
                    "Source": st.column_config.TextColumn("Engine Tier", width="small"),
                },
                hide_index=True,
                use_container_width=True,
                height=380,
            )

        st.markdown("---")
        st.markdown("### Cloud Persistence & Synchronization")
        st.caption("Persist current categorized records to Supabase PostgreSQL (Session Pooler).")

        sync_col1, sync_col2 = st.columns([2, 2])
        with sync_col1:
            if st.button("Sync Ledger to Supabase PostgreSQL", type="primary"):
                with st.spinner("Connecting to Supabase Session Pooler..."):
                    sync_result = upload_expenses_to_supabase(
                        categorized_df, table_name="expenses", if_exists="replace"
                    )
                    if sync_result.get("success"):
                        st.success(
                            f"Successfully synchronized {sync_result.get('rows_uploaded')} records to Supabase table '{sync_result.get('table_name')}'."
                        )
                    else:
                        st.error(f"Sync Failed: {sync_result.get('message')}")

    # --- TAB 4: Enterprise Governance ---
    with tab4:
        st.markdown("### Data Contract & Engineering Governance")
        st.caption("Architectural guarantees, data quality contracts, and efficiency benchmarks.")

        with st.expander("Data Contracts & Pandera Schemas (Fail-Fast)", expanded=True):
            st.markdown(
                """
                Each stage of the data pipeline enforces strict contractual guarantees:
                - `RawTransactionSchema`: Validates `Date` (datetime), `Raw_Description` (str), `Amount` (float, >0), `Type` ('debit'/'credit').
                - `CleanedExpenseSchema`: Ensures non-negative expenses, trimmed merchant descriptions, and formatted ISO dates.
                - `CategorizedExpenseSchema`: Guarantees deterministic categorical classification into one of 10 approved business categories.
                """
            )

        with st.expander("Cost Optimization & SLA Metrics"):
            st.markdown(
                f"""
                - **Total Transactions Processed**: {total_tx}
                - **Heuristic Direct Hits**: {kpi.get('heuristic_count', 0)} ({kpi.get('heuristic_percentage', 0.0)}%)
                - **LLM Calls Saved**: {kpi.get('heuristic_count', 0)} API invocations saved
                - **Analytical Engine Latency**: <1ms per query via in-memory DuckDB columnar storage
                - **Target Cloud Database**: Supabase PostgreSQL on `aws-0-ap-southeast-1.pooler.supabase.com:5432`
                """
            )


if __name__ == "__main__":
    main()
