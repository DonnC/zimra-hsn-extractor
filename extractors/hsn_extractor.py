import os
import csv
import json
import time
import requests
import re
from datetime import datetime
from dotenv import load_dotenv

from .logger import get_logger

logger = get_logger("hsn_extractor")

# =========================================================
# ENV SETUP
# =========================================================

load_dotenv()

BASE_URL = os.getenv("ZIMRA_API_BASE_URL")
AUTH_HEADER = {
    "Authorization": os.getenv("ZIMRA_API_AUTH"),
    "Accept": "application/json",
}

SIM_DATE_RAW = os.getenv("ZIMRA_SIMULATION_DATE")  # e.g. 20260101T00:00
SIM_DATE = datetime.strptime(SIM_DATE_RAW[:8], "%Y%m%d").date()

CSV_FILE = f"data/zimra_hsn_codes_{SIM_DATE}.csv"
PROGRESS_FILE = os.getenv("PROGRESS_FILE", "progress.json")
LOG_FILE = os.getenv("LOG_FILE", "../data/logs/scraper.log")

REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", 0.5))

BASE_PARAMS = {
    "type": int(os.getenv("ZIMRA_CLASSIFICATION_TYPE")),
    "countryId": int(os.getenv("ZIMRA_COUNTRY_ID")),
    "simulationDate": SIM_DATE_RAW,
    "description": "",
    "linkedCode": "",
    "exclusions": "true",
    "dutyTypeId": 0,
}

# =========================================================
# DESCRIPTION CLEANUP HELPERS
# =========================================================

HTML_TAG_RE = re.compile(r"<[^>]+>")
LEADING_JUNK_RE = re.compile(r"^[-\s]+")
MULTISPACE_RE = re.compile(r"\s+")


def normalize_description(desc: str) -> str:
    """
    - Remove HTML tags
    - Remove leading dashes
    - Remove trailing colon
    - Normalize spaces
    - Convert to ALL CAPS
    """
    desc = HTML_TAG_RE.sub("", desc)
    desc = LEADING_JUNK_RE.sub("", desc)
    desc = desc.rstrip(":")
    desc = MULTISPACE_RE.sub(" ", desc)
    return desc.strip().upper()


def is_vague(desc: str) -> bool:
    """
    Descriptions that need enrichment
    """
    return (
        desc == "OTHER"
        or desc.startswith("FOR ")
        or desc.startswith("OF ")
    )


def find_meaningful_parent(code: str, parent_map: dict) -> str | None:
    """
    Walk up the HS hierarchy until a non-vague parent is found
    """
    current = code[:-2]
    while len(current) >= 2:
        parent_desc = parent_map.get(current)
        if parent_desc and not is_vague(parent_desc):
            return parent_desc
        current = current[:-2]
    return None

# =========================================================
# STATE MANAGEMENT
# =========================================================

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_progress(done):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(sorted(done), f, indent=2)


def delete_progress():
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)


def load_existing_codes():
    if not os.path.exists(CSV_FILE):
        return set()

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return {row["hsn_code"] for row in csv.DictReader(f)}


def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["hsn_code", "description"])

# =========================================================
# API CALL
# =========================================================

def fetch(code):
    params = BASE_PARAMS | {"code": code}
    response = requests.get(
        BASE_URL,
        headers=AUTH_HEADER,
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("NationalMeasureCodeLookupList", [])

# =========================================================
# MAIN EXECUTION
# =========================================================

def run():
    init_csv()

    completed_roots = load_progress()
    existing_codes = load_existing_codes()
    parent_map = {}

    logger.info(f"Starting ZIMRA HSN extraction for {SIM_DATE}")
    logger.info(f"Already completed roots: {len(completed_roots)}")
    logger.info(f"Existing codes in CSV: {len(existing_codes)}")

    success = True

    for i in range(1, 100):
        root_code = f"{i:02d}"

        if root_code in completed_roots:
            logger.info(f"Skipping root {root_code} (already processed)")
            continue

        logger.info(f"Processing root code {root_code}")

        try:
            rows = fetch(root_code)
            new_rows = []

            logger.info(f"{root_code}: fetched {len(rows)} records")

            for row in rows:
                code = row.get("NationalMeasureCode")
                raw_desc = row.get("Description", "")

                if not code or not raw_desc:
                    continue

                desc = normalize_description(raw_desc)

                # track hierarchy
                parent_map[code] = desc

                # enrich vague descriptions carefully
                if is_vague(desc):
                    parent_desc = find_meaningful_parent(code, parent_map)
                    if parent_desc and parent_desc not in desc:
                        desc = f"{desc} – {parent_desc}"

                if code not in existing_codes:
                    existing_codes.add(code)
                    new_rows.append({
                        "hsn_code": code,
                        "description": desc
                    })

            if new_rows:
                with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=["hsn_code", "description"]
                    )
                    writer.writerows(new_rows)

                logger.info(f"{root_code}: added {len(new_rows)} new records")
            else:
                logger.info(f"{root_code}: no new records")

            completed_roots.add(root_code)
            save_progress(completed_roots)

            time.sleep(REQUEST_DELAY)

        except Exception as e:
            logger.error(f"FAILED at root {root_code}: {e}")
            success = False
            break

    # =====================================================
    # CLEANUP
    # =====================================================

    if success and len(completed_roots) == 99:
        delete_progress()
        logger.info("All roots processed successfully")
        logger.info("Progress file deleted")
    else:
        logger.warning("Run did not complete fully; progress file retained")

    logger.info("ZIMRA HSN extraction finished")

