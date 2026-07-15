"""
Unit tests for the Intelligent Document Compliance Analyzer.

Run with:
    pytest tests/
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from src.compliance_analyzer import ComplianceAnalyzer
from src.document_parser import parse_document, ParsedDocument
from src.rules_engine import load_rules, evaluate_rule, RuleStatus

RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "rules", "compliance_rules.yaml")
SAMPLE_DOC = os.path.join(os.path.dirname(__file__), "..", "sample_docs", "sample_contract.txt")


@pytest.fixture(scope="module")
def analyzer():
    return ComplianceAnalyzer(RULES_PATH)


@pytest.fixture(scope="module")
def sample_report(analyzer):
    return analyzer.analyze_file(SAMPLE_DOC)


def test_rules_load_correctly():
    rules = load_rules(RULES_PATH)
    assert len(rules) > 0
    ids = [r.id for r in rules]
    assert len(ids) == len(set(ids)), "Rule IDs must be unique"


def test_txt_parser_extracts_text():
    doc = parse_document(SAMPLE_DOC)
    assert isinstance(doc, ParsedDocument)
    assert doc.word_count > 50
    assert "Confidentiality".lower() in doc.full_text.lower() or "confidential" in doc.full_text.lower()


def test_report_has_expected_shape(sample_report):
    assert sample_report.total_rules > 0
    assert 0 <= sample_report.overall_score <= 100
    assert sample_report.passed + sample_report.failed + sample_report.warnings == sample_report.total_rules


def test_confidentiality_clause_passes(sample_report):
    finding = next(f for f in sample_report.findings if f["id"] == "SEC-001")
    assert finding["status"] == "PASS"


def test_termination_clause_passes(sample_report):
    finding = next(f for f in sample_report.findings if f["id"] == "CON-002")
    assert finding["status"] == "PASS"


def test_missing_breach_notification_fails(sample_report):
    # The sample contract has no explicit breach-notification timeline
    finding = next(f for f in sample_report.findings if f["id"] == "SEC-002")
    assert finding["status"] == "FAIL"


def test_prohibited_language_rule_passes_when_absent(sample_report):
    finding = next(f for f in sample_report.findings if f["id"] == "ACC-001")
    assert finding["status"] == "PASS"


def test_keyword_rule_matching_direct():
    rules = load_rules(RULES_PATH)
    rule = next(r for r in rules if r.id == "CON-003")  # Governing Law
    doc = parse_document(SAMPLE_DOC)
    result = evaluate_rule(rule, doc)
    assert result.status == RuleStatus.PASS


def test_category_scores_present(sample_report):
    assert "Data Privacy" in sample_report.category_scores
    assert "Security" in sample_report.category_scores
    assert all(0 <= v <= 100 for v in sample_report.category_scores.values())
