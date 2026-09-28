"""Data Contracts for AI Expense Categorizer.

Ref: ARCH-SCHEMA-01, PRD-REQ-01
Enforces strict schema validation for raw transactions, cleaned expenses,
and final categorized datasets using Pandera.
"""

from typing import Optional
try:
    import pandera.pandas as pa
except ImportError:
    import pandera as pa
from pandera.typing import Series


VALID_CATEGORIES = [
    "F&B",
    "Transportasi",
    "Utilitas",
    "Hiburan",
    "Belanja",
    "Perawatan Kendaraan",
    "Transfer/Tarik Tunai",
    "Kebutuhan Rumah Tangga",
    "Lainnya",
]


class RawTransactionSchema(pa.DataFrameModel):
    """Data Contract for raw transaction files (CSV/Excel ingestion)."""

    Date: Series[str] = pa.Field(
        nullable=False,
        description="Tanggal transaksi dalam format string YYYY-MM-DD",
    )
    Amount: Series[float] = pa.Field(
        ge=0,
        nullable=False,
        coerce=True,
        description="Nominal transaksi wajib bernilai positif atau nol",
    )
    Type: Series[str] = pa.Field(
        isin=["Debit", "Credit", "debit", "credit"],
        nullable=False,
        description="Tipe mutasi rekening (Debit = pengeluaran, Credit = pemasukan)",
    )
    Raw_Description: Series[str] = pa.Field(
        nullable=False,
        str_length={"min_value": 2},
        description="Deskripsi/keterangan mutasi dari bank",
    )

    class Config:
        strict = False
        coerce = True


class CleanedExpenseSchema(pa.DataFrameModel):
    """Data Contract for preprocessed debit/expense transactions."""

    Date: Series[str] = pa.Field(
        nullable=False,
        description="Tanggal pengeluaran format YYYY-MM-DD",
    )
    Amount: Series[float] = pa.Field(
        gt=0,
        nullable=False,
        description="Nominal pengeluaran wajib lebih besar dari 0",
    )
    Raw_Description: Series[str] = pa.Field(
        nullable=False,
        description="Keterangan transaksi asli",
    )

    class Config:
        strict = False
        coerce = True


class CategorizedExpenseSchema(pa.DataFrameModel):
    """Data Contract for final categorized expenses."""

    Date: Series[str] = pa.Field(nullable=False)
    Amount: Series[float] = pa.Field(gt=0, nullable=False)
    Raw_Description: Series[str] = pa.Field(nullable=False)
    Clean_Description: Series[str] = pa.Field(nullable=False)
    Category: Series[str] = pa.Field(
        isin=VALID_CATEGORIES,
        nullable=False,
        description="Kategori pengeluaran terstandarisasi",
    )
    Source: Series[str] = pa.Field(
        isin=["Heuristic_Rules", "Gemini_AI", "Fallback"],
        nullable=False,
        description="Asal penentuan kategori (Rules Tier-1 atau Gemini Tier-2)",
    )

    class Config:
        strict = False
        coerce = True
