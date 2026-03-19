# AI-Powered Trade Document Intelligence

**An AI-powered compliance risk detection system for international trade screening.**

Uses Azure OpenAI (GPT-4o) + multi-algorithm fuzzy matching to screen vendors against OFAC sanctions lists — with specialized Cyrillic transliteration support that catches entity names traditional tools miss.

🔗 **Live Demo:** [https://tatianapodobivskaia-del.github.io/trade-document-intelligence](https://tatianapodobivskaia-del.github.io/trade-document-intelligence)

**Author:** Tatiana Podobivskaia  
**Affiliation:** Atlantis University, Miami, FL  
**Program:** MBA in Business Intelligence & Data Analytics

---

## AI Component

This system integrates AI models via Azure OpenAI to:

- **Analyze vendor entities** against the OFAC SDN list with contextual understanding, not just string matching
- **Detect true vs false positives** — AI identifies when short names or generic words trigger coincidental matches
- **Identify sanctions evasion indicators** — shell companies, unusual transaction patterns, jurisdiction risks
- **Generate natural language reasoning** — every compliance decision comes with an AI explanation
- **Support adaptive risk classification** — beyond static rules, the system learns from entity context

Unlike traditional rule-based systems, this approach enables **adaptive and scalable** compliance screening.

## Why AI — Beyond Rule-Based Systems

| | Traditional Systems | This AI-Powered System |
|---|---|---|
| **Matching** | Static string comparison | Contextual entity analysis via LLM |
| **False Positives** | High rate, manual review | AI filters automatically |
| **Transliteration** | Single spelling only | 3-5 Cyrillic variants generated |
| **Reasoning** | Pass/fail, no explanation | Natural language compliance notes |
| **Cost** | $25K+/year enterprise tools | Serverless, pay-per-use ($0.001/vendor) |
| **Scalability** | Fixed capacity | Auto-scales with Azure Functions |

## Architecture

```
                    ┌─── TWO-PASS ARCHITECTURE ───┐
                    │                              │
Trade Document ──►  │  PASS 1: Pattern Matching    │
(CSV / Manual)      │  • N-gram similarity          │
                    │  • Token sort/set ratio       │
                    │  • Cyrillic transliteration   │
                    │  • Weighted risk scoring      │
                    │  → Instant, in-browser        │
                    │                              │
                    │  PASS 2: AI Deep Analysis     │
                    │  • Azure OpenAI GPT-4o        │
                    │  • True/false positive ID     │
                    │  • Evasion detection          │
                    │  • NL reasoning               │
                    │  → Via Azure Function API     │
                    │                              │
                    └──────────┬───────────────────┘
                               │
                    ┌──────────▼───────────────────┐
                    │   Decision & Audit Trail      │
                    │   APPROVE / FLAG / BLOCK      │
                    │   + AI Confidence Score        │
                    │   + Compliance Recommendation  │
                    └──────────────────────────────┘
```

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| **AI Engine** | Azure OpenAI GPT-4o-mini | Contextual risk analysis, false positive detection |
| **Frontend** | JavaScript, HTML5, Canvas | Interactive screening interface |
| **Backend** | Azure Functions (Python) | Serverless API, AI orchestration |
| **Cloud** | Microsoft Azure (East US) | Hosting, scaling, AI services |
| **Data** | OFAC SDN List (18,712 entities) | U.S. Treasury sanctions database |
| **Transliteration** | Custom Cyrillic Engine | ISO 9, ICAO, BGN/PCGN, informal variants |

## Cyrillic Transliteration — The Technical Gap

A Russian entity name like **"Щербаков"** can appear in trade documents as:

| Variant | System |
|---|---|
| Shcherbakov | ISO 9 / Library of Congress |
| Scherbakov | Simplified / Informal |
| Chtcherbakov | French-influenced |
| Stcherbakov | Older German-influenced |

Standard fuzzy matching treats these as different strings. This system understands they are the **same entity** by applying linguistic rules specific to Russian phonetics.

## Features

- **Real-time OFAC SDN screening** with 18,712+ entities
- **AI-powered risk analysis** via Azure OpenAI GPT-4o
- **Cyrillic transliteration engine** generating 3-5 Latin variants per name
- **Multi-algorithm fuzzy matching** (n-gram, token sort, token set)
- **Weighted risk scoring** (5 factors: name match, country, amount, document type, Cyrillic)
- **Interactive dashboard** with 4 chart types and click-to-enlarge
- **PDF compliance reports** with executive summary and audit trail
- **Batch CSV upload** with drag & drop and smart column detection
- **Risk filters and search** across screening results

## Quick Start

```bash
git clone https://github.com/tatianapodobivskaia-del/trade-document-intelligence.git
cd trade-document-intelligence
pip install -r requirements.txt
python sdn_matcher.py
```

## Relevance

This project addresses priorities identified by:

- **OFAC** — Risk-based sanctions screening programs
- **FinCEN** — Convergence of sanctions, AML, and export controls
- **U.S. CBP** — AI-powered detection of illicit transshipment
- **FATF** — Digital transformation of AML/CFT compliance

## License

Copyright (c) 2026 Tatiana Podobivskaia. All rights reserved. See [LICENSE](LICENSE).

## Contact

Tatiana Podobivskaia  
tatiana.podobivskaia@atlantisuniversity.edu  
[LinkedIn](https://www.linkedin.com/in/tatiana-podobivskaia)
