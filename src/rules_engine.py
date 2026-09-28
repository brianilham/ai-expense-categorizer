"""Deterministic Heuristic Rules Engine (Tier-1 Categorizer).

Ref: ARCH-TECH-01, PRD-SOL-01
Fast in-memory regex matcher (<1ms) for common Indonesian merchants
and recurring bills. Bypasses LLM to save token cost and latency.
"""

import re
from typing import Optional, Tuple


# Regex patterns mapped to standardized categories
RULES = [
    (
        r"\b(PLN|TOKEN PLN|TAGIHAN PLN|PDAM|BPJS|INDIHOME|TELKOM|SPEEDY|BIZNET|FIRSTMEDIA|MYREPUBLIC)\b",
        "Utilitas",
    ),
    (
        r"\b(SPOTIFY|NETFLIX|YOUTUBE|DISNEY\+|HOTSTAR|STEAM|BIOSKOP|XXI|CGV|CINEPOLIS|GRABUNLIMITED)\b",
        "Hiburan",
    ),
    (
        r"\b(KAI|KERETA|COMMUTER|MRT|LRT|TRANSJAKARTA|BLUEBIRD|TAXI|PERTAMINA|SPBU|SHELL|E-TOLL|ETOLL|TOLL|GRAB TRANSPORT|GORIDE|GOCAR)\b",
        "Transportasi",
    ),
    (
        r"\b(WD ATM|TARIK TUNAI|ATM MANDIRI|ATM BCA|ATM BNI|ATM BRI|TOPUP GOPAY|TOPUP OVO|TOPUP DANA|TOPUP SHOPEEPAY|TOPUP LINKAJA|TRF ANTAR BANK)\b",
        "Transfer/Tarik Tunai",
    ),
    (
        r"\b(CARWASH|CUCI MOBIL|CUCI MOTOR|BENGKEL|AHASS|AUTO2000|TAMBAL BAN|GANTI OLI)\b",
        "Perawatan Kendaraan",
    ),
    (
        r"\b(LAUNDRY|SUPERINDO|SAYURBOX|HYPERMART|HERO|FARMERS MARKET|LOTTE|MITRA 10|ACE HARDWARE)\b",
        "Kebutuhan Rumah Tangga",
    ),
    (
        r"\b(SHOPEE|TOKOPEDIA|BLIBLI|LAZADA|INDOMARET|ALFAMART|ALFAMIDI|UNIQLO|H&M|ZARA|MINISO)\b",
        "Belanja",
    ),
    (
        r"\b(KOPI KENANGAN|JANJI JIWA|KOPI HOJA|FORE COFFEE|MIE GACOAN|MCDONALDS|MCD|KFC|STARBUCKS|WARTEG|WAROENK|BORJO|PADANG|HOKBEN|MIXUE|KANTIN)\b",
        "F&B",
    ),
]


def match_heuristic(description: str) -> Tuple[Optional[str], Optional[str]]:
    """Attempt deterministic rule matching.

    Returns:
        (category, "Heuristic_Rules") if matched, else (None, None)
    """
    if not isinstance(description, str) or not description.strip():
        return None, None

    normalized = description.upper()

    for pattern, category in RULES:
        if re.search(pattern, normalized):
            return category, "Heuristic_Rules"

    return None, None
