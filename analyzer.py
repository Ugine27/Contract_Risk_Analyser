"""
Contract Clause Risk Analyzer
==============================
A rule-based NLP system that analyzes legal contract clauses and detects
risk indicators using NLTK, regex, and a weighted keyword dictionary.

Author: Contract Risk Analyzer Project
Compatible with: Python 3.7+, Google Colab
Dependencies: nltk, re, json, collections
"""

import re
import json
import nltk
from collections import defaultdict

# ─── NLTK SETUP ──────────────────────────────────────────────────────────────
# Download required NLTK data packages (safe to run multiple times)
def download_nltk_data():
    """Download all required NLTK corpora silently."""
    packages = ['punkt', 'stopwords', 'punkt_tab']
    for pkg in packages:
        nltk.download(pkg, quiet=True)

download_nltk_data()

from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords


# ─── RISK KEYWORD DICTIONARY ─────────────────────────────────────────────────
# Each entry maps a keyword/phrase to:
#   weight    : numeric risk contribution (1–10)
#   category  : risk type label
#   explanation: plain-English description of why this is risky
RISK_KEYWORDS = {
    # ── Liability & Indemnification ──────────────────────────────────────────
    "indemnify": {
        "weight": 7,
        "category": "Liability",
        "explanation": "Requires one party to compensate the other for losses — can create broad financial exposure."
    },
    "indemnification": {
        "weight": 7,
        "category": "Liability",
        "explanation": "A clause transferring liability from one party to another — risky if uncapped."
    },
    "hold harmless": {
        "weight": 8,
        "category": "Liability",
        "explanation": "Waives right to sue the other party — may eliminate critical legal remedies."
    },
    "unlimited liability": {
        "weight": 10,
        "category": "Liability",
        "explanation": "Exposes a party to uncapped financial loss — one of the highest-risk terms in any contract."
    },

    # ── Termination ──────────────────────────────────────────────────────────
    "terminate": {
        "weight": 5,
        "category": "Termination",
        "explanation": "Grants termination rights — risk depends on which party holds this right and under what conditions."
    },
    "termination for convenience": {
        "weight": 8,
        "category": "Termination",
        "explanation": "Allows termination without cause — provides no contractual stability or notice protection."
    },
    "without cause": {
        "weight": 7,
        "category": "Termination",
        "explanation": "Enables dismissal/termination with no stated reason — highly unfavorable for the receiving party."
    },
    "immediate termination": {
        "weight": 9,
        "category": "Termination",
        "explanation": "Allows instant contract end with no notice — eliminates any wind-down period."
    },
    "notice period": {
        "weight": 3,
        "category": "Termination",
        "explanation": "Specifies how much advance notice is required before termination — shorter periods are riskier."
    },

    # ── Intellectual Property ─────────────────────────────────────────────────
    "intellectual property": {
        "weight": 6,
        "category": "IP Rights",
        "explanation": "Governs ownership of created work — must clarify who owns deliverables."
    },
    "work for hire": {
        "weight": 7,
        "category": "IP Rights",
        "explanation": "Classifies work as employer-owned — creator loses all rights to the work produced."
    },
    "assign": {
        "weight": 5,
        "category": "IP Rights",
        "explanation": "Transfers rights to another party — permanent and often irrevocable."
    },
    "proprietary": {
        "weight": 4,
        "category": "IP Rights",
        "explanation": "Marks information as exclusively owned — mishandling triggers liability."
    },
    "exclusive license": {
        "weight": 6,
        "category": "IP Rights",
        "explanation": "Grants rights to only one party — severely restricts licensor's own use."
    },

    # ── Confidentiality ───────────────────────────────────────────────────────
    "confidential": {
        "weight": 4,
        "category": "Confidentiality",
        "explanation": "Marks information as protected — breach can result in injunctive relief or damages."
    },
    "non-disclosure": {
        "weight": 5,
        "category": "Confidentiality",
        "explanation": "Prohibits sharing specified information — violating this is a serious breach."
    },
    "nda": {
        "weight": 5,
        "category": "Confidentiality",
        "explanation": "Non-Disclosure Agreement reference — check scope, duration, and exclusions carefully."
    },
    "trade secret": {
        "weight": 7,
        "category": "Confidentiality",
        "explanation": "Legally protected proprietary info — accidental disclosure carries statutory penalties."
    },

    # ── Dispute Resolution ────────────────────────────────────────────────────
    "arbitration": {
        "weight": 6,
        "category": "Dispute Resolution",
        "explanation": "Waives right to jury trial — binding arbitration limits appeal rights."
    },
    "governing law": {
        "weight": 4,
        "category": "Dispute Resolution",
        "explanation": "Sets which jurisdiction's law applies — unfavorable jurisdiction adds litigation costs."
    },
    "jurisdiction": {
        "weight": 4,
        "category": "Dispute Resolution",
        "explanation": "Defines where disputes must be resolved — foreign jurisdiction is expensive and inconvenient."
    },
    "class action waiver": {
        "weight": 8,
        "category": "Dispute Resolution",
        "explanation": "Prevents joining group lawsuits — significantly reduces bargaining power for individuals."
    },

    # ── Payment & Penalties ───────────────────────────────────────────────────
    "penalty": {
        "weight": 7,
        "category": "Financial",
        "explanation": "Specifies financial punishment for breach — assess whether penalty is proportionate."
    },
    "liquidated damages": {
        "weight": 6,
        "category": "Financial",
        "explanation": "Pre-agreed breach compensation — may be enforceable even when actual damage is minimal."
    },
    "late payment": {
        "weight": 5,
        "category": "Financial",
        "explanation": "Triggers interest or penalties for delayed payment — clarify rates and grace periods."
    },
    "auto-renewal": {
        "weight": 6,
        "category": "Financial",
        "explanation": "Contract renews automatically — missing opt-out window locks you into another term."
    },
    "price increase": {
        "weight": 5,
        "category": "Financial",
        "explanation": "Permits unilateral price changes — assess whether caps or notice requirements exist."
    },

    # ── Force Majeure & Limitation ────────────────────────────────────────────
    "force majeure": {
        "weight": 4,
        "category": "Force Majeure",
        "explanation": "Excuses performance during unforeseen events — check what qualifies and who benefits."
    },
    "limitation of liability": {
        "weight": 7,
        "category": "Liability",
        "explanation": "Caps what can be recovered — may prevent full compensation for serious harm."
    },
    "waiver": {
        "weight": 5,
        "category": "Rights",
        "explanation": "Gives up a legal right — waivers are often difficult to reverse."
    },
    "sole remedy": {
        "weight": 7,
        "category": "Rights",
        "explanation": "Restricts available legal remedies to one option only — severely limits recourse."
    },

    # ── Non-Compete & Restrictions ────────────────────────────────────────────
    "non-compete": {
        "weight": 7,
        "category": "Restrictions",
        "explanation": "Restricts working for competitors — enforceability varies by jurisdiction."
    },
    "non-solicitation": {
        "weight": 6,
        "category": "Restrictions",
        "explanation": "Prevents poaching clients or employees — can limit post-contract business activity."
    },
    "restraint of trade": {
        "weight": 8,
        "category": "Restrictions",
        "explanation": "Broadly limits business activities — courts often scrutinize these closely."
    },
}


# ─── TEXT PREPROCESSOR ───────────────────────────────────────────────────────

class TextPreprocessor:
    """
    Handles all text cleaning and normalization steps.

    Pipeline:
        raw text → lowercase → clean → tokenize → remove stopwords
    """

    def __init__(self):
        # Load English stopwords from NLTK
        self.stop_words = set(stopwords.words('english'))

        # Keep these legal words even if NLTK marks them as stopwords
        self.legal_preserve = {
            'not', 'no', 'nor', 'without', 'only', 'sole', 'all', 'any',
            'none', 'never', 'shall', 'will', 'must', 'may', 'cannot'
        }

        # Remove preserved legal words from the stopwords set
        self.stop_words -= self.legal_preserve

    def lowercase(self, text: str) -> str:
        """Convert all characters to lowercase for uniform matching."""
        return text.lower()

    def clean(self, text: str) -> str:
        """
        Remove unwanted characters while keeping hyphens (for 'non-compete')
        and apostrophes (for contractions).
        """
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove characters that aren't letters, numbers, spaces, hyphens, apostrophes, or periods
        text = re.sub(r"[^a-z0-9\s\-'.]", ' ', text)
        return text.strip()

    def tokenize(self, text: str) -> list:
        """Split text into individual word tokens using NLTK."""
        return word_tokenize(text)

    def remove_stopwords(self, tokens: list) -> list:
        """Filter out common English words that carry little meaning."""
        return [t for t in tokens if t not in self.stop_words and len(t) > 1]

    def preprocess(self, text: str) -> dict:
        """
        Run the full preprocessing pipeline.

        Returns a dict with each intermediate stage for transparency/debugging.
        """
        lowered = self.lowercase(text)
        cleaned = self.clean(lowered)
        tokens = self.tokenize(cleaned)
        filtered = self.remove_stopwords(tokens)

        return {
            "original": text,
            "lowercased": lowered,
            "cleaned": cleaned,
            "tokens": tokens,
            "filtered_tokens": filtered
        }


# ─── RISK SCORER ─────────────────────────────────────────────────────────────

class RiskScorer:
    """
    Scores a contract clause by matching it against the risk keyword dictionary.

    Matching strategy:
        1. Single-word token match (fast, handles stemming variation)
        2. Multi-word phrase match via regex on the cleaned text (handles 'hold harmless')
    """

    # Risk tier thresholds (cumulative score)
    THRESHOLDS = {
        "Low":    (0,  14),
        "Medium": (15, 29),
        "High":   (30, float('inf'))
    }

    def __init__(self):
        self.keywords = RISK_KEYWORDS

        # Separate single-word and multi-word phrases for efficient matching
        self.single_words = {k: v for k, v in self.keywords.items() if ' ' not in k and '-' not in k}
        self.phrases      = {k: v for k, v in self.keywords.items() if ' ' in k or '-' in k}

    def match_single_words(self, tokens: list) -> list:
        """
        Check each filtered token against single-word risk keywords.

        Returns a list of match dicts.
        """
        matches = []
        seen = set()  # Avoid counting the same keyword twice per clause

        for token in tokens:
            if token in self.single_words and token not in seen:
                seen.add(token)
                info = self.single_words[token]
                matches.append({
                    "keyword": token,
                    "weight": info["weight"],
                    "category": info["category"],
                    "explanation": info["explanation"]
                })

        return matches

    def match_phrases(self, cleaned_text: str) -> list:
        """
        Search for multi-word phrases using regex on the cleaned, lowercased text.

        Returns a list of match dicts.
        """
        matches = []
        seen = set()

        for phrase, info in self.phrases.items():
            # Build a regex that allows flexible whitespace between words
            pattern = r'\b' + r'\s+'.join(re.escape(word) for word in phrase.split()) + r'\b'
            if re.search(pattern, cleaned_text) and phrase not in seen:
                seen.add(phrase)
                matches.append({
                    "keyword": phrase,
                    "weight": info["weight"],
                    "category": info["category"],
                    "explanation": info["explanation"]
                })

        return matches

    def calculate_score(self, matches: list) -> int:
        """Sum the weights of all matched keywords to produce a raw risk score."""
        return sum(m["weight"] for m in matches)

    def classify_risk(self, score: int) -> str:
        """Map a numeric score to a Low / Medium / High risk tier."""
        for tier, (low, high) in self.THRESHOLDS.items():
            if low <= score <= high:
                return tier
        return "High"  # Default for very high scores

    def score_clause(self, preprocessed: dict) -> dict:
        """
        Run the full scoring pipeline on a preprocessed clause.

        Args:
            preprocessed: output dict from TextPreprocessor.preprocess()

        Returns:
            dict with matches, score, risk tier, and per-category breakdown.
        """
        tokens       = preprocessed["filtered_tokens"]
        cleaned_text = preprocessed["cleaned"]

        # Collect matches from both strategies
        single_matches = self.match_single_words(tokens)
        phrase_matches = self.match_phrases(cleaned_text)

        # Deduplicate: if a phrase already caught a word, skip the word match
        phrase_keywords = {m["keyword"] for m in phrase_matches}
        single_matches  = [m for m in single_matches if m["keyword"] not in phrase_keywords]

        all_matches = phrase_matches + single_matches

        # Aggregate by category
        categories = defaultdict(list)
        for match in all_matches:
            categories[match["category"]].append(match["keyword"])

        score     = self.calculate_score(all_matches)
        risk_tier = self.classify_risk(score)

        return {
            "matches":        all_matches,
            "total_score":    score,
            "risk_level":     risk_tier,
            "categories":     dict(categories),
            "keyword_count":  len(all_matches)
        }


# ─── EXPLANATION BUILDER ─────────────────────────────────────────────────────

class ExplanationBuilder:
    """
    Converts raw scoring results into human-readable explanations.
    These are the 'why was this flagged?' responses for each clause.
    """

    RISK_SUMMARIES = {
        "Low":    "This clause contains minor risk indicators. Review recommended but not urgent.",
        "Medium": "This clause has notable risk factors. Legal review is advisable before signing.",
        "High":   "This clause carries significant legal risk. Do NOT sign without expert review."
    }

    def build_flags(self, matches: list) -> list:
        """
        Convert each keyword match into a structured flag object with a
        human-readable reason.
        """
        flags = []
        for match in matches:
            flags.append({
                "flagged_term":  match["keyword"],
                "risk_category": match["category"],
                "risk_weight":   f"{match['weight']}/10",
                "reason":        match["explanation"]
            })
        # Sort flags by weight descending so the most dangerous appear first
        flags.sort(key=lambda x: int(x["risk_weight"].split('/')[0]), reverse=True)
        return flags

    def build_summary(self, risk_level: str, score: int, categories: dict) -> str:
        """
        Compose a plain-English summary paragraph for the clause.
        """
        base = self.RISK_SUMMARIES[risk_level]
        category_list = ', '.join(categories.keys()) if categories else 'none'
        return (
            f"{base} "
            f"Risk score: {score}. "
            f"Risk categories detected: {category_list}."
        )

    def build(self, scoring_result: dict, clause_id: str) -> dict:
        """
        Assemble the final explanation object for one clause.
        """
        return {
            "clause_id":      clause_id,
            "risk_level":     scoring_result["risk_level"],
            "risk_score":     scoring_result["total_score"],
            "summary":        self.build_summary(
                                  scoring_result["risk_level"],
                                  scoring_result["total_score"],
                                  scoring_result["categories"]
                              ),
            "flags":          self.build_flags(scoring_result["matches"]),
            "categories":     scoring_result["categories"],
            "keywords_found": scoring_result["keyword_count"]
        }


# ─── MAIN ANALYZER ───────────────────────────────────────────────────────────

class ContractRiskAnalyzer:
    """
    Top-level orchestrator that ties together preprocessing, scoring,
    and explanation for one or more contract clauses.

    Usage:
        analyzer = ContractRiskAnalyzer()
        result   = analyzer.analyze("The contractor shall indemnify...")
        print(json.dumps(result, indent=2))
    """

    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.scorer        = RiskScorer()
        self.explainer     = ExplanationBuilder()

    def analyze_clause(self, clause: str, clause_id: str = "clause_1") -> dict:
        """
        Analyze a single contract clause end-to-end.

        Data flow:
            clause (str)
              → TextPreprocessor.preprocess()   → preprocessed dict
              → RiskScorer.score_clause()       → scoring dict
              → ExplanationBuilder.build()      → explanation dict
              → final result dict

        Args:
            clause    : Raw clause text string.
            clause_id : Identifier label for this clause (default 'clause_1').

        Returns:
            A structured dict with preprocessing info + full risk analysis.
        """
        # Step 1 — Preprocess
        preprocessed = self.preprocessor.preprocess(clause)

        # Step 2 — Score
        scoring = self.scorer.score_clause(preprocessed)

        # Step 3 — Explain
        explanation = self.explainer.build(scoring, clause_id)

        # Step 4 — Assemble final output
        return {
            "clause_id":       clause_id,
            "original_text":   clause,
            "preprocessing": {
                "token_count":          len(preprocessed["tokens"]),
                "filtered_token_count": len(preprocessed["filtered_tokens"]),
                "sample_tokens":        preprocessed["filtered_tokens"][:10]
            },
            "risk_analysis":   explanation
        }

    def analyze_contract(self, clauses: list) -> dict:
        """
        Analyze multiple clauses and produce a contract-level summary.

        Args:
            clauses: List of dicts with keys 'id' and 'text', e.g.:
                     [{"id": "clause_1", "text": "The vendor shall..."}]

        Returns:
            Full contract analysis with per-clause results and an overall summary.
        """
        results   = []
        all_scores = []
        risk_counts = {"Low": 0, "Medium": 0, "High": 0}

        for clause in clauses:
            clause_id   = clause.get("id", f"clause_{len(results)+1}")
            clause_text = clause.get("text", "")

            result = self.analyze_clause(clause_text, clause_id)
            results.append(result)

            score = result["risk_analysis"]["risk_score"]
            level = result["risk_analysis"]["risk_level"]
            all_scores.append(score)
            risk_counts[level] += 1

        # Contract-level metrics
        overall_score = sum(all_scores)
        avg_score     = round(overall_score / len(all_scores), 2) if all_scores else 0
        overall_risk  = self.scorer.classify_risk(overall_score)

        return {
            "contract_summary": {
                "total_clauses":        len(clauses),
                "overall_risk_level":   overall_risk,
                "overall_risk_score":   overall_score,
                "average_clause_score": avg_score,
                "clause_risk_breakdown": risk_counts,
                "recommendation":       ExplanationBuilder.RISK_SUMMARIES[overall_risk]
            },
            "clause_results": results
        }
