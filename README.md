# ZIMRA HSN Code Extractor

This repository provides a **reliable, resumable data extraction utility** for obtaining
Zimbabwe tariff / HSN codes and descriptions for downstream compliance and ERP usage.

Get upto-date info and more on [ZIMRA website](https://etariff.zimra.co.zw/#)

Check out the last run [hsn codes here (csv)](data/)

---

## 🎯 Purpose

- Extract **tariff classification codes and descriptions**
- Produce a **clean CSV dataset**
- Support **restartable execution** for large datasets
- Enable **offline usage** once extracted

---

## 📦 Output Format

```csv
hsn_code,description
84021910,Fire-tube and other shell boilers
84029000,Parts of boilers
84042000,Condensers for steam or other vapour power units
````

---

## ⚙️ Features

* Incremental persistence (crash-safe)
* Deduplication by code
* Configurable via environment variables
* Polite request pacing
* Full execution logging

---

## 🧩 Requirements

* Python 3.9+
* pip

---

## 🔧 Installation

```bash
git clone https://github.com/DonnC/zimra-hsn-extractor.git
cd zimra-hsn-scrapper
pip install -r requirements.txt
```

---

## 🔐 Configuration

Create a `.env` file in the project root:

```env
ZIMRA_API_BASE_URL=...
ZIMRA_API_AUTH=...
ZIMRA_COUNTRY_ID=252
ZIMRA_CLASSIFICATION_TYPE=163
ZIMRA_SIMULATION_DATE=YYYYMMDDT00:00
REQUEST_DELAY=0.4
```
---

## ▶️ Usage

```bash
python scraper.py
```

The script can be safely stopped and restarted at any time.
Progress is automatically resumed.

---

## 📁 Generated Files

| File                  | Purpose           |
| --------------------- | ----------------- |
| `zimra_hsn_codes.csv` | Extracted dataset |
| `progress.json`       | Resume state      |
| `logs/scraper.log`    | Execution log     |

---

## ⚠️ Disclaimer

This tool is intended for **internal data synchronization, research, and compliance workflows**.
Users are responsible for ensuring usage aligns with applicable laws, terms, and policies.

> Data is provided as is, with no guarantee of accuracy or upto-date

---

## 🏗️ Intended Integration

* ERP systems
* Customs & trade compliance tools
* Reporting & analytics pipelines
