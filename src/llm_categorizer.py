"""LLM Batch Categorizer (Tier-2 Categorizer via Google Gemini).

Ref: ARCH-TECH-01, PRD-SOL-01
Uses Gemini 3.5 Flash Lite with batch prompting to categorize ambiguous,
local, and unique transaction descriptions.
"""

import json
import os
import re
from typing import List
from dotenv import load_dotenv
import google.generativeai as genai
from src.schemas import VALID_CATEGORIES

load_dotenv(override=True)


def get_gemini_model():
    """Initialize and return Gemini generative model."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY tidak ditemukan di environment atau file .env!"
        )
    genai.configure(api_key=api_key, transport="rest")
    # Preferred lightweight model
    return genai.GenerativeModel("gemini-3.5-flash-lite")


def categorize_batch_with_llm(
    descriptions: List[str], batch_size: int = 40
) -> List[str]:
    """Categorize a list of transaction descriptions in batches.

    Ref: PRD-SOL-01
    """
    if not descriptions:
        return []

    try:
        model = get_gemini_model()
    except Exception as e:
        print(f"Warning: Gemini API initialization failed ({e}). Using Fallback.")
        return ["Lainnya"] * len(descriptions)

    categories_result: List[str] = []

    for i in range(0, len(descriptions), batch_size):
        chunk = descriptions[i : i + batch_size]

        prompt = f"""
Kamu adalah asisten pengklasifikasi mutasi finansial otomatis.
Kategorikan setiap transaksi berikut secara tepat ke SALAH SATU kategori ini:
{json.dumps(VALID_CATEGORIES, ensure_ascii=False)}

Daftar Transaksi:
{json.dumps(chunk, ensure_ascii=False)}

ATURAN WAJIB:
1. Keluarkan HANYA JSON array string berisi nama kategori dengan urutan yang sama persis sejumlah {len(chunk)} item.
2. Jangan berikan teks pembuka atau penjelasan apapun.
Contoh:
["F&B", "Utilitas", "Hiburan"]
"""
        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            # Clean markdown codeblocks
            clean_json = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
            clean_json = re.sub(r"\s*```$", "", clean_json)
            parsed = json.loads(clean_json)

            if isinstance(parsed, list) and len(parsed) == len(chunk):
                # Sanitize against valid categories
                sanitized = [
                    cat if cat in VALID_CATEGORIES else "Lainnya"
                    for cat in parsed
                ]
                categories_result.extend(sanitized)
            else:
                # If length mismatch, fill chunk with fallback
                print(f"Warning: LLM returned unexpected length {len(parsed)} vs {len(chunk)}.")
                categories_result.extend(["Lainnya"] * len(chunk))
        except Exception as e:
            print(f"Warning: Batch LLM categorization error ({e}). Using Fallback.")
            categories_result.extend(["Lainnya"] * len(chunk))

    return categories_result
