"""Indonesian Banking Mutation Data Generator.

Ref: PRD-DATA-01, ARCH-TECH-01
Generates 150+ realistic Indonesian bank and e-wallet transactions (BCA, Mandiri,
GoPay, ShopeePay, QRIS) for testing and benchmarking.
"""

import random
from datetime import datetime, timedelta
import pandas as pd
from src.schemas import RawTransactionSchema


MERCHANT_POOL = [
    # F&B
    ("QRIS KOPI KENANGAN", 28000, 45000, "Debit", "F&B"),
    ("QRIS JANJI JIWA", 22000, 38000, "Debit", "F&B"),
    ("QRIS MIE GACOAN", 35000, 65000, "Debit", "F&B"),
    ("TRF KANTIN RAYA", 15000, 30000, "Debit", "F&B"),
    ("QRIS WAROENK PENGKOLAN", 20000, 45000, "Debit", "F&B"),
    ("QRIS KOPI HOJA", 25000, 35000, "Debit", "F&B"),
    ("TRF WARTEG BAHARI", 18000, 32000, "Debit", "F&B"),
    ("QRIS MIXUE ICE CREAM", 16000, 28000, "Debit", "F&B"),
    ("EDC RM PADANG SEDERHANA", 75000, 160000, "Debit", "F&B"),
    ("QRIS FORE COFFEE", 32000, 52000, "Debit", "F&B"),
    ("TRF BORJO MURNI", 12000, 25000, "Debit", "F&B"),
    # Transportasi
    ("GRAB TRANSPORT G-9182", 18000, 65000, "Debit", "Transportasi"),
    ("GOJEK GORIDE TRIP-881", 14000, 38000, "Debit", "Transportasi"),
    ("TIKET KERETA KAI KAI-8921X", 185000, 450000, "Debit", "Transportasi"),
    ("TOPUP KMT COMMUTER LINE", 50000, 100000, "Debit", "Transportasi"),
    ("BLUEBIRD TAXI B-1928", 45000, 120000, "Debit", "Transportasi"),
    ("SPBU PERTAMINA PASTI PAS", 50000, 250000, "Debit", "Transportasi"),
    ("SPBU SHELL V-POWER", 100000, 300000, "Debit", "Transportasi"),
    ("TOPUP E-TOLL MANDIRI", 100000, 200000, "Debit", "Transportasi"),
    # Utilitas
    ("PAYMENT PLN TOKEN", 100000, 250000, "Debit", "Utilitas"),
    ("TAGIHAN PLN POSTPAID", 250000, 500000, "Debit", "Utilitas"),
    ("PAYMENT PDAM SURYA", 65000, 140000, "Debit", "Utilitas"),
    ("PAYMENT BPJS KESEHATAN", 70000, 150000, "Debit", "Utilitas"),
    ("INDIHOME TELKOM SPEEDY", 380000, 450000, "Debit", "Utilitas"),
    ("BIZNET HOME INTERNET", 375000, 375000, "Debit", "Utilitas"),
    # Hiburan
    ("SPOTIFY PREMIUM", 54900, 54900, "Debit", "Hiburan"),
    ("NETFLIX SUBSCRIPTION", 186000, 186000, "Debit", "Hiburan"),
    ("YOUTUBE PREMIUM FAMILY", 99000, 99000, "Debit", "Hiburan"),
    ("TIKET BIOSKOP XXI CINEMA", 80000, 160000, "Debit", "Hiburan"),
    ("STEAM GAMES PURCHASE", 75000, 450000, "Debit", "Hiburan"),
    ("GRABUNLIMITED SUB", 45000, 45000, "Debit", "Hiburan"),
    # Belanja
    ("SHOPEE PAY INV-9912", 45000, 350000, "Debit", "Belanja"),
    ("TOKOPEDIA MP INV-8821", 85000, 550000, "Debit", "Belanja"),
    ("INDOMARET POINT", 25000, 110000, "Debit", "Belanja"),
    ("ALFAMART RETAIL", 20000, 95000, "Debit", "Belanja"),
    ("UNIQLO GRAND INDONESIA", 299000, 899000, "Debit", "Belanja"),
    ("MINISO INDONESIA", 49000, 175000, "Debit", "Belanja"),
    # Perawatan Kendaraan
    ("ORANGE CARWASH", 60000, 120000, "Debit", "Perawatan Kendaraan"),
    ("CUCI MOTOR KILAT", 20000, 35000, "Debit", "Perawatan Kendaraan"),
    ("BENGKEL RESMI AHASS HONDA", 120000, 450000, "Debit", "Perawatan Kendaraan"),
    ("TAMBAL BAN TUBELESS EXPRESS", 25000, 45000, "Debit", "Perawatan Kendaraan"),
    # Kebutuhan Rumah Tangga
    ("EVERYDAY LAUNDRY KILOAN", 45000, 95000, "Debit", "Kebutuhan Rumah Tangga"),
    ("SUPERINDO FRESH MARKET", 150000, 420000, "Debit", "Kebutuhan Rumah Tangga"),
    ("SAYURBOX ONLINE GROCERY", 85000, 210000, "Debit", "Kebutuhan Rumah Tangga"),
    # Transfer / Tarik Tunai
    ("WD ATM MANDIRI", 100000, 1000000, "Debit", "Transfer/Tarik Tunai"),
    ("WD ATM BCA", 100000, 1500000, "Debit", "Transfer/Tarik Tunai"),
    ("TOPUP GOPAY DRIVER/WALLET", 50000, 300000, "Debit", "Transfer/Tarik Tunai"),
    ("TOPUP OVO SALDO", 50000, 250000, "Debit", "Transfer/Tarik Tunai"),
    ("TRF ANTAR BANK KE REK BCA", 100000, 1000000, "Debit", "Transfer/Tarik Tunai"),
    # Pemasukan (Credit)
    ("PAYROLL PT MAJU BERSAMA", 8500000, 12000000, "Credit", "Income"),
    ("TRF MASUK BONUS PROJECT", 1500000, 3000000, "Credit", "Income"),
    ("CASHBACK PROMO SHOPEE", 10000, 50000, "Credit", "Income"),
    ("BUNGA TABUNGAN BANK", 5000, 15000, "Credit", "Income"),
]


def generate_synthetic_transactions(
    num_transactions: int = 160,
    start_date: str = "2026-08-01",
    seed: int = 42,
) -> pd.DataFrame:
    """Generate realistic Indonesian bank mutation transactions.

    Ref: PRD-DATA-01
    """
    random.seed(seed)
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")

    records = []
    # Always guarantee payroll at beginning and mid-month
    records.append({
        "Date": start_dt.strftime("%Y-%m-%d"),
        "Amount": 10000000.0,
        "Type": "Credit",
        "Raw_Description": "PAYROLL PT MAJU BERSAMA",
    })

    for i in range(1, num_transactions):
        # Pick random day across 60 days
        day_offset = random.randint(0, 59)
        tx_date = (start_dt + timedelta(days=day_offset)).strftime("%Y-%m-%d")

        item = random.choice(MERCHANT_POOL)
        desc, min_amt, max_amt, tx_type, _ = item

        # Round amounts to neat thousands
        raw_amt = random.randint(min_amt, max_amt)
        rounded_amt = float(round(raw_amt, -3) if raw_amt > 10000 else raw_amt)

        # Optional suffix/invoice noise
        noise = ""
        if "INV" in desc or "TRIP" in desc or "G-" in desc or "KAI-" in desc:
            noise = f" #{random.randint(100, 999)}"

        records.append({
            "Date": tx_date,
            "Amount": rounded_amt,
            "Type": tx_type,
            "Raw_Description": f"{desc}{noise}",
        })

    df = pd.DataFrame(records)
    # Sort chronologically
    df["Date_dt"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date_dt").drop(columns=["Date_dt"]).reset_index(drop=True)

    # Validate against Pandera RawTransactionSchema
    validated_df = RawTransactionSchema.validate(df)
    return validated_df


if __name__ == "__main__":
    df = generate_synthetic_transactions(160)
    out_path = "synthetic_transactions.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} validated transactions saved to {out_path}!")
    print(df.head(10))
