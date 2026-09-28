"""Unit tests for Bank Statement Ingestion and Auto-detection Parsers."""

import pytest
import pandas as pd
from src.parsers import parse_mandiri_statement, load_statement_file
from src.schemas import RawTransactionSchema

SAMPLE_MANDIRI_DATA = """e-Statement;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;;;;;;;;;;;;
;;;;;;;;;;;;;Menara Mandiri 1 Jalan Jenderal Sudirman Kav. 54-55, Jakarta 12190, Indonesia;;;;;;;;;;;
Nama/Name;;;;;:;BRIAN ILHAM HERMATRISTAN ;;;;;Periode/Period;:    ;01 Sep 2026 - 22 Sep 2026;;;;;;;;;;;
Cabang/Branch;;;;;:;KC Bekasi Menara Mandiri;;;;;Dicetak pada/Issued on;:;23 Sep 2026;;;;;;;;;;;
Tabungan NOW IDR;;;;;;;;;;;;;;;;Saldo Awal/Initial Balance;;;;;2.540.398,46;;;
;;;;;;;;;;;;;;;;Dana Masuk/Incoming Transactions;;;;;10.800.000,00;;;
Nomor Rekening/Account Number;;;;;;;;:;1560017211907;;;;;;;Dana Keluar/Outgoing Transactions;;;;;9.630.620,00;;;
Mata Uang/Currency;;;;;;;;:;IDR;;;;;;;Saldo Akhir/Closing Balance;;;;;3.709.778,46;;;
;No;;;Tanggal;;;Keterangan;;;;;;;;Dana Masuk (IDR);;;Dana Keluar (IDR);;;Saldo (IDR);;;
;No;;;Date;;;Remarks;;;;;;;;Incoming Transactions (IDR);;;Outgoing Transactions (IDR);;;Balance (IDR);;;
1;;;;01 Sep 2026;;;"Transaksi e-Commerce
VAP-SHOPEE";;;;;;;;;;;41.920,00;;;2.498.478,46;;;
;;;;09:39:37 WIB;;;;;;;;;;;;;;;;;;;;
2;;;;02 Sep 2026;;;"Transaksi e-Commerce
VAP-APPLE.COM";;;;;;;;;;;36.000,00;;;2.462.478,46;;;
;;;;13:11:35 WIB;;;;;;;;;;;;;;;;;;;;
3;;;;02 Sep 2026;;;"Pembayaran QR
ke Coda Payments
609429656677";;;;;;;;;;;12.000,00;;;2.450.478,46;;;
;;;;14:50:08 WIB;;;;;;;;;;;;;;;;;;;;
4;;;;03 Sep 2026;;;Biaya administrasi kartu debit;;;;;;;;;;;6.000,00;;;2.444.478,46;;;
;;;;05:45:26 WIB;;;;;;;;;;;;;;;;;;;;
8;;;;08 Sep 2026;;;"Transfer dari BANK MANDIRI
TRI UTOMO 1560009925985";;;;;;;;700.000,00;;;;;;2.995.478,46;;;
;;;;11:15:17 WIB;;;;;;;;;;;;;;;;;;;;
;;;;;;;PT Bank Mandiri (Persero) Tbk. berizin dan diawasi oleh Otoritas Jasa Keuangan (OJK);;;;;;;;;;;;Mandiri Call 14000;;;;;
"""

def test_parse_mandiri_statement():
    df = parse_mandiri_statement(SAMPLE_MANDIRI_DATA)
    # Must adhere strictly to RawTransactionSchema
    validated = RawTransactionSchema.validate(df)
    assert len(validated) == 5
    assert (validated["Type"] == "Debit").sum() == 4
    assert (validated["Type"] == "Credit").sum() == 1
    # Check date formatting
    assert validated.iloc[0]["Date"] == "2026-09-01"
    assert validated.iloc[0]["Amount"] == 41920.0
    assert validated.iloc[4]["Type"] == "Credit"
    assert validated.iloc[4]["Amount"] == 700000.0

def test_load_statement_file_autodetect():
    df = load_statement_file(SAMPLE_MANDIRI_DATA)
    assert len(df) == 5
    assert set(df.columns) == {"Date", "Raw_Description", "Amount", "Type"}
