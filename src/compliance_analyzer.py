"""
compliance_analyzer.py
-----------------------
Top-level orchestrator: parses a document, runs it against the rule set,
and produces a structured compliance report (score + findings).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any

from .document_parser import parse_document, ParsedDocument
from .rules_engine import load_rules, evaluate_all, RuleResult, RuleStatus, SEVERITY_WEIGHTS


@dataclass
class ComplianceReport:
    filename: str
    generated_at: str
    overall_score: float
    total_rules: int
    passed: int
    failed: int
    warnings: int
    category_scores: Dict[str, float]
    findings: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ComplianceAnalyzer:
    def __init__(self, rules_path: str):
        self.rules_path = rules_path
        self.rules = load_rules(rules_path)

    def analyze_file(self, file_path: str) -> ComplianceReport:
        doc = parse_document(file_path)
        return self.analyze_document(doc)

    def analyze_document(self, doc: ParsedDocument) -> ComplianceReport:
        results = evaluate_all(self.rules, doc)
        return self._build_report(doc, results)

    def _build_report(self, doc: ParsedDocument, results: List[RuleResult]) -> ComplianceReport:
        passed = sum(1 for r in results if r.status == RuleStatus.PASS)
        failed = sum(1 for r in results if r.status == RuleStatus.FAIL)
        warnings = sum(1 for r in results if r.status == RuleStatus.WARNING)

        # Weighted score: PASS = full weight, WARNING = half weight, FAIL = 0
        total_weight = sum(SEVERITY_WEIGHTS[r.rule.severity] for r in results) or 1
        earned_weight = 0.0
        for r in results:
            w = SEVERITY_WEIGHTS[r.rule.severity]
            if r.status == RuleStatus.PASS:
                earned_weight += w
            elif r.status == RuleStatus.WARNING:
                earned_weight += w * 0.5

        overall_score = round((earned_weight / total_weight) * 100, 1)

        # Per-category breakdown
        categories: Dict[str, List[RuleResult]] = {}
        for r in results:
            categories.setdefault(r.rule.category, []).append(r)

        category_scores = {}
        for cat, cat_results in categories.items():
            cat_total = sum(SEVERITY_WEIGHTS[r.rule.severity] for r in cat_results) or 1
            cat_earned = sum(
                SEVERITY_WEIGHTS[r.rule.severity] if r.status == RuleStatus.PASS
                else (SEVERITY_WEIGHTS[r.rule.severity] * 0.5 if r.status == RuleStatus.WARNING else 0)
                for r in cat_results
            )
            category_scores[cat] = round((cat_earned / cat_total) * 100, 1)

        findings = [
            {
                "id": r.rule.id,
                "category": r.rule.category,
                "title": r.rule.title,
                "description": r.rule.description,
                "severity": r.rule.severity,
                "status": r.status.value,
                "confidence": r.score,
                "evidence": r.evidence,
            }
            for r in results
        ]
        # Surface failures and warnings first for readability
        severity_order = {"critical": 0, "major": 1, "minor": 2}
        status_order = {"FAIL": 0, "WARNING": 1, "PASS": 2}
        findings.sort(key=lambda f: (status_order[f["status"]], severity_order[f["severity"]]))

        return ComplianceReport(
            filename=doc.filename,
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            overall_score=overall_score,
            total_rules=len(results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            category_scores=category_scores,
            findings=findings,
        )
