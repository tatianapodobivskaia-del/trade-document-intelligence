# TradeScreenAI

## AI-Powered Multi-List Sanctions Screening with Cyrillic Transliteration

🔗 **Live Demo:** [tradescreenai.com](https://tradescreenai.com)

An AI-driven sanctions screening system that screens vendors against **4 international sanctions lists** (45,296+ entities) with specialized Cyrillic-to-Latin transliteration and GPT-4o deep analysis. This prototype was developed as the final project for the Information Technology Systems course. All work was performed individually as part of academic requirements.

**Author:** Tatiana Podobivskaia  
**Affiliation:** Atlantis University, Miami, FL  
**Program:** MBA in Business Intelligence & Data Analytics

---

## Sanctions Lists

| List | Source | Entities | Update |
|------|--------|----------|--------|
| OFAC SDN | U.S. Treasury | 18,714 | Daily |
| EU Consolidated | European Union | 5,819 | Daily |
| UN Security Council | United Nations | 1,002 | Daily |
| UK OFSI | UK Government | 19,761 | Daily |
| **Total** | **4 Lists** | **45,296** | |

## Key Features

- **Multi-list screening** — simultaneous screening across OFAC SDN, EU, UN, and UK OFSI sanctions lists
- **Cyrillic transliteration engine** — generates 2–5 Latin-script variants per name using ISO 9, ICAO, BGN/PCGN, and informal systems
- **Two-pass architecture** — Pattern Matching (instant, in-browser) + AI Deep Analysis (Azure OpenAI GPT-4o)
- **Multi-algorithm fuzzy matching** — composite scoring using token sort, token set, partial, and standard ratio
- **Alias matching** — checks entity aliases from all 4 lists
- **PDF compliance reports** — auto-generated with executive summary, risk breakdown, and audit trail
- **Risk-based routing** — automated APPROVE / FLAG / BLOCK with configurable thresholds

## Problem

- Existing enterprise compliance tools are often cost-prohibitive for academic research environments, motivating this prototype approach.
- **Cyrillic transliteration creates detection gaps** — "Щербаков" can appear as Shcherbakov, Scherbakov, Shtcherbakov, or Shherbakov
- **Single-list screening is insufficient** — sanctioned entities may appear on EU/UN/UK lists but not OFAC

## Cyrillic Transliteration

| Variant | System |
|---------|--------|
| Shcherbakov | ISO 9 |
| Scherbakov | Simplified / Informal |
| Shtcherbakov | Passport-style |
| Schtscherbakov | German-influenced |

Standard tools treat these as different entities. TradeScreenAI generates all variants and matches against all 4 lists simultaneously.

## Architecture

```
Trade Document (CSV / Single Vendor)
        │
        ▼
   Entity Extraction
        │
        ▼
Cyrillic Transliteration ──► Generate 2–5 Latin variants
        │
        ▼
Multi-List Screening ──► OFAC SDN + EU + UN + UK OFSI (45,296 entities + aliases)
        │
        ▼
   Composite Risk Score
        │
        ├── LOW  (< 50)  ──► Auto-approve, Log
        ├── MED  (50–84) ──► Flag, Notify compliance officer
        └── HIGH (≥ 85)  ──► Block, Escalate
        │
        ▼
   AI Deep Analysis (Azure OpenAI GPT-4o)
        │
        ▼
   PDF Compliance Report
```

## Quick Start

### Installation

```bash
git clone https://github.com/tatianapodobivskaia-del/trade-document-intelligence.git
cd trade-document-intelligence
pip install -r requirements.txt
```

### Run Multi-List Screening Demo

```bash
python sdn_matcher.py
```

This will:
- Download all 4 sanctions lists (OFAC SDN, EU, UN, UK OFSI)
- Demonstrate Cyrillic transliteration variants
- Screen 7 sample vendors against 45,296 entities
- Export results to CSV and JSON

### Screen Your Own Vendors

```python
from sanctions_lists import load_all_sanctions_lists
from sdn_matcher import screen_vendor

data = load_all_sanctions_lists()
result = screen_vendor("Rosoboronexport Trading", data["entities"],
                       cyrillic_name="Рособоронэкспорт Трейдинг")
print(result)
```

## Project Structure

```
trade-document-intelligence/
├── index.html              # Web interface (tradescreenai.com)
├── sanctions_lists.py      # Multi-list loader (OFAC + EU + UN + UK OFSI)
├── sdn_matcher.py          # Screening engine with transliteration
├── privacy.html            # Privacy Policy
├── terms.html              # Terms of Service
├── disclaimer.html         # Compliance Disclaimer
├── requirements.txt        # Python dependencies
├── sample_vendors.csv      # Test data
├── screening_results.csv   # Output (generated)
├── screening_results.json  # JSON export (generated)
└── README.md
```

## Technology Stack

- **Python** — Screening engine and transliteration
- **Microsoft Azure** — Cloud infrastructure (Functions, OpenAI)
- **Azure OpenAI GPT-4o** — AI deep analysis for true/false positive classification
- **Vercel** — Web hosting and CDN
- **OFAC, EU, UN, UK OFSI** — Official government sanctions data

## Risk Scoring

Composite score (0–100) from multiple algorithms:

| Algorithm | Weight | Strength |
|-----------|--------|----------|
| Token Sort Ratio | 30% | Handles word order differences |
| Token Set Ratio | 30% | Handles extra/missing words |
| Partial Ratio | 25% | Catches substring matches |
| Standard Ratio | 15% | Overall string similarity |

**Weighted Composite:** Name Match (75%) + Country Risk (10%) + Amount (5%) + Document Type (5%) + Cyrillic Bonus (5%)

## Dependencies

```
requests
fuzzywuzzy
python-Levenshtein
transliterate
pandas
```

## Disclaimer

TradeScreenAI is a research prototype developed as part of graduate-level coursework. It is a decision-support tool for informational and educational purposes only. It does not constitute legal or compliance advice. See [disclaimer](https://tradescreenai.com/disclaimer.html).

## License

Copyright © 2026 Tatiana Podobivskaia. All rights reserved. This software is proprietary. Unauthorized copying, modification, or distribution is prohibited.

## Contact

Tatiana Podobivskaia  
Email: tatiana.podobivskaia@atlantisuniversity.edu  
Website: [tradescreenai.com](https://tradescreenai.com)  
LinkedIn: [linkedin.com/in/tatiana-podobivskaia](https://www.linkedin.com/in/tatiana-podobivskaia)

