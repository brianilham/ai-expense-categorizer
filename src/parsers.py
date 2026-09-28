"""Bank Statement Ingestion and Auto-Detection Parsers.

Ref: PRD-DATA-01, ARCH-FLOW-01
Supports standard 4-column CSV as well as raw Indonesian bank e-Statements (e.g. Bank Mandiri).
"""

from typing import Union, BinaryIO, TextIO
import csv
import io
import re
import pandas as pd
from src.schemas import RawTransactionSchema

MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "mei": "05", "may": "05",
    "jun": "06", "jul": "07", "agu": "08", "aug": "08", "sep": "09", "okt": "10",
    "oct": "10", "nov": "11", "des": "12", "dec": "12"
}


def parse_mandiri_statement(raw_text: str) -> pd.DataFrame:
    """Parse raw Bank Mandiri e-Statement CSV with semicolon delimiter and metadata headers."""
    # Strip potential UTF-8 BOM
    if raw_text.startswith("\ufeff"):
        raw_text = raw_text[1:]

    # Mandiri CSV exports use semicolon ';'
    reader = csv.reader(io.StringIO(raw_text), delimiter=";")
    rows = list(reader)

    # 1. Locate the transaction table header
    header_idx = -1
    for i, row in enumerate(rows):
        joined = " ".join(row).lower()
        if "tanggal" in joined and "keterangan" in joined:
            header_idx = i
            break

    if header_idx == -1:
        raise ValueError(
            "Format e-Statement Mandiri tidak memiliki baris header mutasi (Tanggal, Keterangan)."
        )

    header_row = rows[header_idx]

    # Map column positions dynamically from header row
    col_date = 4
    col_desc = 7
    col_in = 15
    col_out = 18

    for c_i, c_val in enumerate(header_row):
        val_lower = c_val.lower()
        if "tanggal" in val_lower or "date" in val_lower:
            col_date = c_i
        elif "keterangan" in val_lower or "remarks" in val_lower:
            col_desc = c_i
        elif "dana masuk" in val_lower or "incoming" in val_lower:
            col_in = c_i
        elif "dana keluar" in val_lower or "outgoing" in val_lower:
            col_out = c_i

    records = []
    current_tx = None

    start_row = header_idx + 1
    # Skip bilingual header row if present
    if start_row < len(rows) and any("date" in c.lower() for c in rows[start_row]):
        start_row += 1

    for row in rows[start_row:]:
        non_empty = [c.strip() for c in row if c.strip()]
        if not non_empty:
            continue

        # Check for footer disclaimer
        if any("bank mandiri" in c.lower() for c in non_empty) and any("ojk" in c.lower() for c in non_empty):
            break
        if any("mandiri call" in c.lower() for c in non_empty):
            break

        first_val = non_empty[0]

        # New numbered transaction row (e.g. '1', '2', '3')
        if first_val.isdigit():
            if current_tx:
                records.append(current_tx)

            # Date extraction
            date_raw = ""
            if len(row) > col_date and row[col_date].strip():
                date_raw = row[col_date].strip()
            elif len(non_empty) > 1 and any(m in non_empty[1].lower() for m in MONTH_MAP):
                date_raw = non_empty[1]

            # Parse date "01 Sep 2026" to "2026-09-01"
            date_formatted = date_raw
            d_parts = date_raw.split()
            if len(d_parts) == 3 and d_parts[1].lower()[:3] in MONTH_MAP:
                month_num = MONTH_MAP[d_parts[1].lower()[:3]]
                day_num = int(d_parts[0])
                year_num = d_parts[2]
                date_formatted = f"{year_num}-{month_num}-{day_num:02d}"

            # Description extraction
            desc_raw = ""
            if len(row) > col_desc and row[col_desc].strip():
                desc_raw = row[col_desc].strip()
            elif len(non_empty) > 2:
                desc_raw = non_empty[2]

            # In/Out amount parsing
            in_val_str = row[col_in].strip() if len(row) > col_in else ""
            out_val_str = row[col_out].strip() if len(row) > col_out else ""

            tx_type = "Debit"
            amount = 0.0

            if out_val_str:
                clean_num = out_val_str.replace(".", "").replace(",", ".")
                try:
                    amount = float(clean_num)
                    tx_type = "Debit"
                except ValueError:
                    pass
            elif in_val_str:
                clean_num = in_val_str.replace(".", "").replace(",", ".")
                try:
                    amount = float(clean_num)
                    tx_type = "Credit"
                except ValueError:
                    pass
            else:
                # Scan row for valid currency pattern
                for c in row:
                    c_clean = c.strip()
                    if re.match(r"^\d{1,3}(\.\d{3})*,\d{2}$", c_clean):
                        amount = float(c_clean.replace(".", "").replace(",", "."))
                        tx_type = "Debit"
                        break

            current_tx = {
                "Date": date_formatted,
                "Raw_Description": desc_raw.replace("\n", " ").strip(),
                "Amount": amount,
                "Type": tx_type,
            }
        else:
            # Continuation row (multiline merchant remarks or timestamp)
            if current_tx:
                text_continuation = " ".join(
                    [c for c in non_empty if not re.match(r"^\d{1,3}(\.\d{3})*,\d{2}$", c)]
                )
                # Ignore timestamp rows like '09:39:37 WIB'
                if not re.search(r"\d{2}:\d{2}:\d{2}\s*wib", text_continuation.lower()):
                    if text_continuation and text_continuation != "-":
                        current_tx["Raw_Description"] += " " + text_continuation

    if current_tx:
        records.append(current_tx)

    df_out = pd.DataFrame(records)
    if df_out.empty:
        raise ValueError("Tidak ada transaksi valid yang ditemukan di dalam e-Statement Mandiri.")

    # Filter out empty descriptions or zero amounts
    df_out = df_out[(df_out["Amount"] > 0) & (df_out["Raw_Description"].str.len() >= 3)]
    df_out = df_out.reset_index(drop=True)

    # Validate against Pandera schema
    return RawTransactionSchema.validate(df_out)


def load_statement_file(file_obj: Union[str, io.BytesIO, io.StringIO, BinaryIO, TextIO]) -> pd.DataFrame:
    """Smart ingestion parser that auto-detects delimiter and bank statement layout."""
    # Read raw content to string
    if isinstance(file_obj, str):
        import os
        if os.path.exists(file_obj):
            with open(file_obj, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        else:
            content = file_obj
    elif isinstance(file_obj, (io.BytesIO, BinaryIO)):
        content = file_obj.read().decode("utf-8", errors="replace")
    elif isinstance(file_obj, (io.StringIO, TextIO)):
        content = file_obj.read()
    else:
        # Streamlit UploadedFile has .getvalue()
        if hasattr(file_obj, "getvalue"):
            val = file_obj.getvalue()
            content = val.decode("utf-8", errors="replace") if isinstance(val, bytes) else str(val)
        else:
            content = str(file_obj)

    # 1. Check if this is a Bank Mandiri e-Statement
    content_lower = content[:2000].lower()
    if "mandiri" in content_lower or "dana masuk" in content_lower or (";" in content[:300] and "e-statement" in content_lower):
        return parse_mandiri_statement(content)

    # 2. Otherwise try standard CSV with automatic delimiter sniffing
    try:
        # Sniff delimiter (; or , or \t)
        sample_chunk = content[:4096]
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample_chunk)
        sep = dialect.delimiter
    except Exception:
        sep = ","

    df = pd.read_csv(io.StringIO(content), sep=sep)
    # Check if standard columns exist
    required_cols = {"Date", "Raw_Description", "Amount", "Type"}
    if required_cols.issubset(set(df.columns)):
        return RawTransactionSchema.validate(df)

    # If columns don't match, raise informative message
    raise ValueError(
        f"Format CSV tidak dikenali. Kolom yang ditemukan: {list(df.columns)}. "
        "Harap unggah CSV standar (Date, Raw_Description, Amount, Type) atau e-Statement Bank Mandiri resmi."
    )
