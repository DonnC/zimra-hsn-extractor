# ZIMRA Extractors
A modular data extraction toolkit for Zimbabwe Revenue Authority (ZIMRA) documents.

This project extracts structured compliance data from official ZIMRA PDFs and converts them into machine-readable formats (CSV) for integration with ERP systems such as ERPNext.

---

## 🚀 Purpose

ZIMRA publishes compliance data in different format:

* PAYE tax tables
* Tariff / HSN codes
* VAT rates
* Customs duty schedules

These are not API-ready.

This project converts them into structured datasets for:

* System automation=
* VAT automation
* Compliance dashboards
* Data versioning & archiving

---

## 📂 Project Structure

```
zimra-extractors/
├── extractors/
├── data/
│   ├── raw/
│   ├── processed/
│   └── logs/
├── main.py
└── README.md
```

---

## 📌 Current Extractors

### 1️⃣ HSN Extractor

Extracts tariff / commodity codes from ZIMRA publications.

Output:

```
data/processed/hsn_<year>.csv
```

### 2️⃣ PAYE Tax Table Extractor

Extracts:

* Income ranges
* Tax rate %
* Deduct amount
* AIDS levy %
* Currency
* Frequency (Daily, Weekly, Monthly, etc.)
* Year metadata

Output:

```
data/processed/zimra_paye_tables_<year>.csv
```

## 🧾 Output Format (PAYE)

`currency | frequency | year | month_from | month_to | income_from | income_to | rate_percent | deduct_amount | aids_levy_percent`

---

## ▶️ Usage

Place ZIMRA PDFs into:

```
data/raw/
```

Run:

```
python main.py
```

Extracted files will appear in:

```
data/processed/
```

Logs:

```
data/logs/zimra_extractors.log
```



## ⚖️ Compliance Notice

This tool does not alter official tax data.
It only restructures publicly issued ZIMRA documents into machine-readable formats.

Always verify outputs against official publications.