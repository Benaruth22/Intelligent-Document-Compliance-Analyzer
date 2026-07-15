"""
rules_engine.py
----------------
Loads compliance rules from YAML and evaluates them against a parsed document
using keyword, regex, or TF-IDF semantic-similarity matching.
"""

from __future__ import annotations

import re
import yaml
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .document_parser import ParsedDocument


class RuleStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


SEVERITY_WEIGHTS = {"critical": 3, "major": 2, "minor": 1}


@dataclass
class Rule:
    id: str
    category: str
    title: str
    description: str
    strategy: str
    severity: str
    keywords: List[str] = field(default_factory=list)
    pattern: Optional[str] = None
    reference_text: Optional[str] = None
    threshold: float = 0.2
    prohibited: bool = False

    @classmethod
    def from_dict(cls, d: dict) -> "Rule":
        return cls(
            id=d["id"],
            category=d.get("category", "General"),
            title=d.get("title", d["id"]),
            description=d.get("description", ""),
            strategy=d["strategy"],
            severity=d.get("severity", "minor"),
            keywords=d.get("keywords", []),
            pattern=d.get("pattern"),
            reference_text=d.get("reference_text"),
            threshold=d.get("threshold", 0.2),
            prohibited=d.get("prohibited", False),
        )


@dataclass
class RuleResult:
    rule: Rule
    status: RuleStatus
    evidence: str = ""
    score: float = 0.0  # similarity / match confidence, where applicable


def load_rules(path: str) -> List[Rule]:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return [Rule.from_dict(r) for r in raw]


def _match_keyword(rule: Rule, doc: ParsedDocument) -> RuleResult:
    text_lower = doc.full_text.lower()
    for kw in rule.keywords:
        if kw.lower() in text_lower:
            if rule.prohibited:
                idx = text_lower.find(kw.lower())
                snippet = doc.full_text[max(0, idx - 40): idx + len(kw) + 40]
                return RuleResult(rule, RuleStatus.FAIL, evidence=snippet.strip(), score=1.0)
            idx = text_lower.find(kw.lower())
            snippet = doc.full_text[max(0, idx - 40): idx + len(kw) + 40]
            return RuleResult(rule, RuleStatus.PASS, evidence=snippet.strip(), score=1.0)

    if rule.prohibited:
        return RuleResult(rule, RuleStatus.PASS, evidence="No prohibited terms found.", score=0.0)
    return RuleResult(rule, RuleStatus.FAIL, evidence="No matching keywords found.", score=0.0)


def _match_regex(rule: Rule, doc: ParsedDocument) -> RuleResult:
    match = re.search(rule.pattern, doc.full_text, re.IGNORECASE | re.DOTALL)
    if match:
        snippet = doc.full_text[max(0, match.start() - 30): match.end() + 30]
        return RuleResult(rule, RuleStatus.PASS, evidence=snippet.strip(), score=1.0)
    return RuleResult(rule, RuleStatus.FAIL, evidence="Pattern not found.", score=0.0)


def _match_semantic(rule: Rule, doc: ParsedDocument) -> RuleResult:
    paragraphs = doc.paragraphs or [doc.full_text]
    corpus = paragraphs + [rule.reference_text]

    try:
        vectorizer = TfidfVectorizer(stop_words="english").fit(corpus)
        vectors = vectorizer.transform(corpus)
        ref_vector = vectors[-1]
        para_vectors = vectors[:-1]
        similarities = cosine_similarity(para_vectors, ref_vector).flatten()
    except ValueError:
        # Empty vocabulary (e.g. doc is entirely stopwords/numbers)
        return RuleResult(rule, RuleStatus.FAIL, evidence="Insufficient text to evaluate.", score=0.0)

    best_idx = similarities.argmax()
    best_score = float(similarities[best_idx])
    best_paragraph = paragraphs[best_idx]

    if best_score >= rule.threshold:
        status = RuleStatus.PASS
    elif best_score >= rule.threshold * 0.5:
        status = RuleStatus.WARNING
    else:
        status = RuleStatus.FAIL

    return RuleResult(rule, status, evidence=best_paragraph[:300], score=round(best_score, 3))


def evaluate_rule(rule: Rule, doc: ParsedDocument) -> RuleResult:
    if rule.strategy == "keyword":
        return _match_keyword(rule, doc)
    if rule.strategy == "regex":
        return _match_regex(rule, doc)
    if rule.strategy == "semantic":
        return _match_semantic(rule, doc)
    raise ValueError(f"Unknown rule strategy: {rule.strategy}")


def evaluate_all(rules: List[Rule], doc: ParsedDocument) -> List[RuleResult]:
    return [evaluate_rule(rule, doc) for rule in rules]
