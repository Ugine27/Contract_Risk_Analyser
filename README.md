# 📄 Contract Clause Risk Analyzer

> **Rule-based NLP system for legal contract risk detection**  
> Built with Python · NLTK · Regex — No LLMs, No APIs, No Black Boxes

---

## What It Does

The **Contract Clause Risk Analyzer** scans individual contract clauses and identifies legal risk indicators using interpretable, rule-based NLP. It produces a structured JSON report that explains *what* was flagged, *why* it's risky, and *how severe* the risk is.

This project is designed to be:
- **Colab-compatible** — runs in Google Colab with zero setup friction  
- **Transparent** — no hidden model weights, no API calls
- **Extensible** — add new keywords in one place

---

## Tech Stack

| Component          | Technology                  |
|--------------------|-----------------------------|
| Language           | Python 3.7+                 |
| NLP Library        | NLTK                        |
| Pattern Matching   | `re` (Python regex)         |
| Output Format      | JSON                        |
| Notebook           | Google Colab / Jupyter      |

---

## 🗂️ Project Structure

```
contract_risk_analyzer/
│
├── analyzer.py                  # Core engine (preprocessor + scorer + explainer)
├── Contract_Risk_Analyzer.ipynb # Google Colab notebook (self-contained)
├── sample_data.json             # Sample inputs & expected outputs
├── requirements.txt             # pip dependencies
└── README.md                    # This file
```

---


## Pipeline Overview

```
Raw Clause Text
       │
       ▼
┌─────────────────┐
│ TextPreprocessor│  lowercase → clean → tokenize → remove stopwords
└────────┬────────┘
         │ preprocessed dict
         ▼
┌─────────────────┐
│   RiskScorer    │  single-word match + phrase regex match → score → tier
└────────┬────────┘
         │ scoring dict
         ▼
┌────────────────────┐
│ ExplanationBuilder │  flags + summary + categories
└────────┬───────────┘
         │
         ▼
     JSON Output
```

---

## Sample Output

**Input:**
```
"The contractor shall indemnify and hold harmless the Company from any claims. 
The Company may terminate this agreement immediately and without cause."
```

**Output (abbreviated):**
```json
{
  "clause_id": "termination_clause",
  "risk_level": "High",
  "risk_score": 37,
  "summary": "Significant legal risk. Do NOT sign without expert review. Score: 37.",
  "flags": [
    {
      "flagged_term": "hold harmless",
      "risk_category": "Liability",
      "risk_weight": "8/10",
      "reason": "Waives right to sue — may eliminate critical legal remedies."
    },
    {
      "flagged_term": "without cause",
      "risk_category": "Termination",
      "risk_weight": "7/10",
      "reason": "Enables dismissal with no reason — highly unfavorable."
    },
    {
      "flagged_term": "indemnify",
      "risk_category": "Liability",
      "risk_weight": "7/10",
      "reason": "Requires one party to compensate the other for losses."
    }
  ],
  "categories": {
    "Liability": ["hold harmless", "indemnify"],
    "Termination": ["without cause", "terminate"]
  }
}
```

---

## Risk Keyword Categories

| Category          | Example Keywords                                          |
|-------------------|-----------------------------------------------------------|
| Liability         | `indemnify`, `hold harmless`, `unlimited liability`       |
| Termination       | `termination for convenience`, `without cause`, `immediate termination` |
| IP Rights         | `work for hire`, `intellectual property`, `exclusive license` |
| Confidentiality   | `trade secret`, `non-disclosure`, `nda`                   |
| Dispute Resolution| `arbitration`, `class action waiver`, `governing law`     |
| Financial         | `penalty`, `liquidated damages`, `auto-renewal`           |
| Restrictions      | `non-compete`, `non-solicitation`, `restraint of trade`   |

---

## Risk Scoring System

| Tier   | Score Range | Meaning                                          |
|--------|-------------|--------------------------------------------------|
| Low    | 0 – 4      | Minor indicators, routine review recommended     |
| Medium | 5 – 14     | Notable risks, legal review advisable            |
| High   | 15+         | Significant exposure, expert review required     |

Scores are the **sum of keyword weights** (each keyword weighted 1–10).

---

## How to Extend

Add new risk keywords in `analyzer.py` under `RISK_KEYWORDS`:


---

## Future Improvements

- **TF-IDF weighting** — weight terms by rarity across a corpus of contracts
- **Sentence-level output** — highlight the exact sentence containing each risk
- **Negation detection** — distinguish "shall not indemnify" from "shall indemnify"
- **Severity modifiers** — boost score when risk words co-occur (e.g. "unlimited" + "liability")
- **HTML/PDF report export** — generate a formatted risk report
- **Streamlit web UI** — drag-and-drop contract analysis interface
- **Domain-specific dictionaries** — employment, SaaS, real estate variants

---


