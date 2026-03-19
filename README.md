# AI-Powered Trade Document Intelligence
## Live Demo

🔗 https://tatianapodobivskaia-del.github.io/trade-document-intelligence/## 
Automated Sanctions Screening with Cyrillic Transliteration Support

An AI-driven trade document screening system that analyzes vendor and supplier data against the OFAC SDN (Specially Designated Nationals) list, with specialized fuzzy matching for Cyrillic-to-Latin transliteration variants. Designed for small and medium-sized enterprises (SMEs) engaged in cross-border procurement.

**Author:** Tatiana Podobivskaia
**Affiliation:** Atlantis University, Miami, FL
**Program:** MBA in Business Intelligence & Data Analytics

---

## Problem

International trade relies on accurate screening of counterparties against sanctions lists. Current challenges include:

- **Enterprise tools are too expensive for SMEs** — solutions like NICE Actimize or Dow Jones Risk & Compliance cost tens of thousands of dollars annually
- **AI-generated document fraud is rising** — generative AI can now produce convincing fake invoices, bills of lading, and certificates of origin
- **Cyrillic transliteration creates detection gaps** — Russian entity names can appear in 3-5 different Latin spellings across trade documents, and standard matching algorithms miss these variations

## Solution

This system provides:

1. **Real-time OFAC SDN screening** — downloads and parses the official U.S. Treasury sanctions list
2. **Multi-algorithm fuzzy matching** — composite scoring using token sort, token set, partial, and standard ratio algorithms
3. **Cyrillic transliteration engine** — generates multiple Latin-script variants based on ISO 9, BGN/PCGN, passport, and informal transliteration systems
4. **Risk-based routing** — automated approve / flag / block decisions with configurable thresholds
5. **Power BI integration** — JSON export for real-time compliance dashboard visualization

## Cyrillic Transliteration — The Technical Gap

A Russian entity name like **"Щербаков"** can appear in trade documents as:

| Variant | Transliteration System |
|---------|----------------------|
| Shcherbakov | ISO 9 / Library of Congress |
| Scherbakov | Simplified / Informal |
| Chtcherbakov | French-influenced |
| Stcherbakov | Older German-influenced |

Standard fuzzy matching treats these as different strings. This system understands they are the **same entity** by applying linguistic rules specific to Russian phonetics and morphology.

## Architecture

```
Trade Document (CSV/Excel)
        |
        v
   Entity Extraction
        |
        v
Cyrillic Transliteration --> Generate 3-5 Latin variants
        |
        v
OFAC SDN Cross-Reference --> Fuzzy matching (composite score)
        |
        v
   Risk Scoring Engine
        |
        |-- LOW (< 50%)  --> Auto-approve, Log
        |-- MED (50-85%) --> Flag, Notify compliance officer
        |-- HIGH (> 85%) --> Block, Escalate, Alert
        |
        v
   Power BI Dashboard
```

## Quick Start

### Installation

```bash
git clone https://github.com/[your-username]/trade-document-intelligence.git
cd trade-document-intelligence
pip install -r requirements.txt
```

### Run Demo

```bash
python sdn_matcher.py
```

This will:
- Download the latest OFAC SDN list from U.S. Treasury
- Demonstrate Cyrillic transliteration variants
- Screen 7 sample vendors with varying risk levels
- Export results to CSV and JSON

### Screen Your Own Vendors

Prepare a CSV file with columns: `vendor_name`, `country`, `amount`, `document_type`, `cyrillic_name` (optional)

```python
from sdn_matcher import download_sdn_list, parse_sdn_list, screen_vendor_file

raw = download_sdn_list()
sdn = parse_sdn_list(raw)
results = screen_vendor_file("your_vendors.csv", sdn)
print(results)
```

## Project Structure

```
trade-document-intelligence/
├── sdn_matcher.py          # Core matching engine
├── requirements.txt        # Python dependencies
├── sample_vendors.csv      # Test data
├── screening_results.csv   # Output (generated)
├── screening_results.json  # Power BI export (generated)
└── README.md
```

## Dependencies

```
requests
fuzzywuzzy
python-Levenshtein
transliterate
pandas
```

## Technology Stack

- **Python** — Core screening engine
- **Microsoft Azure** — Cloud infrastructure (Blob Storage, Functions)
- **Power Automate** — Workflow orchestration
- **Power BI** — Compliance dashboard
- **OFAC SDN API** — Official U.S. Treasury sanctions data

## Risk Scoring Methodology

The system uses a composite similarity score (0-100) combining four algorithms:

| Algorithm | Weight | Strength |
|-----------|--------|----------|
| Token Sort Ratio | 30% | Handles word order differences |
| Token Set Ratio | 30% | Handles extra/missing words |
| Partial Ratio | 25% | Catches substring matches |
| Standard Ratio | 15% | Overall string similarity |

Thresholds are configurable:
- **HIGH risk (>= 85%):** Transaction blocked, escalated for manual review
- **MEDIUM risk (50-84%):** Flagged for compliance officer review
- **LOW risk (< 50%):** Auto-approved, logged for audit trail

## Relevance

This project addresses priorities identified by:
- **OFAC** — Risk-based sanctions screening programs
- **FinCEN** — Convergence of sanctions, AML, and export controls
- **U.S. CBP** — AI-powered detection of illicit transshipment
- **FATF** — Digital transformation of AML/CFT compliance


## Contact

Tatiana Podobivskaia
tatiana.podobivskaia@atlantisuniversity.edu
[LinkedIn](https://www.linkedin.com/in/tatiana-podobivskaia)

## Copyright

© 2026 Tatiana Podobivskaia. All rights reserved.

This project and its code are proprietary. No part of this project may be copied, modified, or distributed without explicit permission from the author.
