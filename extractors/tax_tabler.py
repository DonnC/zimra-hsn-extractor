import os
import re
import pdfplumber
import pandas as pd
from datetime import datetime
from .logger import get_logger

logger = get_logger("tax_tabler")

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

AIDS_LEVY_PERCENT = 3.0

def clean_number(value):
    if not value:
        return None
    value = value.replace(",", "").strip()
    value = re.sub(r"[^\d\.]", "", value)
    if value in ["", "."]:
        return None
    return float(value)

def compute_currency(pdf_path):
    if "USD" in pdf_path:
        return "USD"

    if "ZWG" in pdf_path:
        return "ZWG"

    return "UNKNOWN"

def extract_from_pdf(pdf_path):
    logger.info(f"Processing PDF: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    currency = compute_currency(pdf_path)
    year_match = re.search(r"(20\d{2})", full_text)
    year = int(year_match.group(1)) if year_match else datetime.now().year

    month_from, month_to = 1, 12

    frequencies = ["DAILY", "WEEKLY", "FORTNIGHTLY", "MONTHLY", "ANNUAL"]

    rows = []

    pattern = re.compile(
        r"from\s+([\d,\.]+)?\s*(?:to\s+([\d,\.]+))?\s*multiply\s+by\s+(\d+)%\s*Deduct\s+([\d,\.\-]+)?",
        re.IGNORECASE
    )

    for freq in frequencies:
        if freq in full_text.upper():
            logger.info(f"Extracting frequency: {freq}")
            section_parts = re.split(freq, full_text, flags=re.IGNORECASE)
            section_text = section_parts[1] if len(section_parts) > 1 else full_text

            for match in pattern.finditer(section_text):
                income_from = clean_number(match.group(1))
                income_to = clean_number(match.group(2))
                rate = float(match.group(3))
                deduct = clean_number(match.group(4)) or 0

                rows.append({
                    "currency": currency,
                    "frequency": freq.title(),
                    "year": year,
                    "month_from": month_from,
                    "month_to": month_to,
                    "income_from": income_from,
                    "income_to": income_to,
                    "rate_percent": rate,
                    "deduct_amount": deduct,
                    "aids_levy_percent": AIDS_LEVY_PERCENT
                })

    return rows


def run():
    logger.info("Starting PAYE tax table extraction")

    os.makedirs(PROCESSED_DIR, exist_ok=True)

    all_rows = []

    for filename in os.listdir(RAW_DIR):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(RAW_DIR, filename)
            rows = extract_from_pdf(path)
            all_rows.extend(rows)

    if not all_rows:
        logger.warning("No tax data extracted")
        return

    df = pd.DataFrame(all_rows)
    df.sort_values(["currency", "frequency", "income_from"], inplace=True)

    year = df["year"].iloc[0]
    output_file = os.path.join(
        PROCESSED_DIR,
        f"zimra_paye_tables_{year}.csv"
    )

    df.to_csv(output_file, index=False)

    logger.info(f"Extraction complete. Saved to {output_file}")
