#!/usr/bin/env python3
"""
cli.py
------
Command-line entry point for the Intelligent Document Compliance Analyzer.

Usage:
    python cli.py --file sample_docs/sample_contract.txt
    python cli.py --file contract.pdf --rules rules/compliance_rules.yaml --out reports/
    python cli.py --file contract.docx --format pdf json html
"""

import argparse
import os
import sys

from src.compliance_analyzer import ComplianceAnalyzer
from src.report_generator import save_json, save_html, save_pdf


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a document (PDF/DOCX/TXT) for compliance against a configurable rule set."
    )
    parser.add_argument("--file", required=True, help="Path to the document to analyze.")
    parser.add_argument(
        "--rules", default="rules/compliance_rules.yaml", help="Path to the YAML rule definitions."
    )
    parser.add_argument("--out", default="reports", help="Output directory for generated reports.")
    parser.add_argument(
        "--format", nargs="+", default=["html", "json"], choices=["html", "json", "pdf"],
        help="Which report format(s) to generate."
    )
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)

    print(f"Analyzing '{args.file}' against rules in '{args.rules}'...")
    analyzer = ComplianceAnalyzer(args.rules)
    report = analyzer.analyze_file(args.file)

    base_name = os.path.splitext(os.path.basename(args.file))[0]

    print("\n=== Compliance Summary ===")
    print(f"File:            {report.filename}")
    print(f"Overall Score:   {report.overall_score}%")
    print(f"Rules Checked:   {report.total_rules}")
    print(f"Passed:          {report.passed}")
    print(f"Warnings:        {report.warnings}")
    print(f"Failed:          {report.failed}")
    print("\nBy Category:")
    for cat, score in report.category_scores.items():
        print(f"  - {cat:<22} {score}%")

    if "json" in args.format:
        path = save_json(report, os.path.join(args.out, f"{base_name}_report.json"))
        print(f"\nSaved JSON report -> {path}")
    if "html" in args.format:
        path = save_html(report, os.path.join(args.out, f"{base_name}_report.html"))
        print(f"Saved HTML report -> {path}")
    if "pdf" in args.format:
        path = save_pdf(report, os.path.join(args.out, f"{base_name}_report.pdf"))
        print(f"Saved PDF report  -> {path}")


if __name__ == "__main__":
    main()
