# 📋 Intelligent Document Compliance Analyzer

An NLP-powered tool that automatically reviews contracts, policies, and agreements (PDF, DOCX, or TXT) against a configurable rule set — flagging missing clauses, compliance gaps, and prohibited language — and generates a scored, shareable report.

Built to demonstrate: document processing pipelines, rule-engine design, lightweight NLP (TF-IDF semantic matching), automated report generation, and a usable end-user interface (CLI + Streamlit dashboard).

---

## ✨ Features

- **Multi-format ingestion** — parses `.pdf`, `.docx`, and `.txt` documents, including table content in Word docs.
- **Hybrid rule engine** — combines three matching strategies:
  - **Keyword matching** for explicit required/prohibited terms
  - **Regex matching** for structured requirements (e.g. "breach notification within N days")
  - **Semantic similarity (TF-IDF + cosine similarity)** to catch clauses that are present but phrased differently than expected
- **Weighted compliance scoring** — findings are weighted by severity (`critical` / `major` / `minor`) and rolled up into an overall score and per-category breakdown.
- **Configurable rules** — all checks live in a single [`rules/compliance_rules.yaml`](rules/compliance_rules.yaml) file covering Data Privacy, Security, Contract Terms, Financial Compliance, Liability, and Accessibility — extend or edit without touching code.
- **Report exports** — JSON (for pipelines/APIs), styled HTML (for sharing), and PDF (for filing/records).
- **Two interfaces** — a scriptable CLI for batch/automation use, and a Streamlit dashboard for interactive, drag-and-drop analysis.
- **Tested** — unit test suite covering parsing, rule evaluation, and scoring logic.

---

## 🏗️ Architecture

```
Document (PDF/DOCX/TXT)
        │
        ▼
 document_parser.py   → extracts & normalizes text, paragraphs
        │
        ▼
 rules_engine.py       → evaluates each rule (keyword / regex / semantic)
        │
        ▼
 compliance_analyzer.py → aggregates results into a weighted score + findings
        │
        ▼
 report_generator.py   → renders JSON / HTML / PDF report
        │
        ▼
  cli.py  /  app.py     → command-line or Streamlit interface
```

---

## 📁 Project Structure

```
intelligent-document-compliance-analyzer/
├── app.py                        # Streamlit dashboard
├── cli.py                        # Command-line interface
├── requirements.txt
├── rules/
│   └── compliance_rules.yaml     # Editable rule definitions
├── sample_docs/
│   └── sample_contract.txt       # Demo document with intentional gaps
├── src/
│   ├── document_parser.py        # PDF/DOCX/TXT text extraction
│   ├── rules_engine.py           # Rule loading + matching strategies
│   ├── compliance_analyzer.py    # Scoring + report assembly
│   └── report_generator.py       # JSON/HTML/PDF rendering
├── tests/
│   └── test_compliance_analyzer.py
└── reports/                      # Generated output (gitignored)
```

---

## 🚀 Getting Started

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run via CLI
```bash
python cli.py --file sample_docs/sample_contract.txt --format html json pdf
```

Output:
```
=== Compliance Summary ===
File:            sample_contract.txt
Overall Score:   82.6%
Rules Checked:   11
Passed:          9
Warnings:        0
Failed:          2

By Category:
  - Data Privacy           60.0%
  - Security               60.0%
  - Contract Terms         100.0%
  - Financial Compliance   100.0%
  - Liability              100.0%
  - Accessibility          100.0%

Saved JSON report -> reports/sample_contract_report.json
Saved HTML report -> reports/sample_contract_report.html
Saved PDF report  -> reports/sample_contract_report.pdf
```

### 3. Run the interactive dashboard
```bash
streamlit run app.py
```
Upload any `.pdf`, `.docx`, or `.txt` file to get an instant score, category breakdown, expandable findings with evidence snippets, and one-click HTML/PDF export.

### 4. Run tests
```bash
pytest tests/ -v
```

---

## 🔧 Customizing the Rules

Rules live in `rules/compliance_rules.yaml`. Each rule declares a matching `strategy`:

```yaml
- id: SEC-002
  category: "Security"
  title: "Data Breach Notification"
  description: "Document must specify a breach notification procedure and timeline."
  strategy: regex
  pattern: "notify.{0,40}(breach|incident).{0,60}(\\d+\\s*(hours|days))"
  severity: major
```

Add new rules, adjust severity weighting, or swap in your organization's own required clauses (e.g. HIPAA, SOX, GDPR-specific language) without changing any code.

---

## 🧠 Design Notes / Why This Approach

- **TF-IDF over full transformer embeddings**: keeps the tool dependency-light and runnable fully offline/air-gapped — a realistic constraint in legal/compliance environments — while still catching paraphrased clauses that pure keyword search would miss.
- **Severity-weighted scoring** instead of a flat pass/fail count, so a single missing critical clause (e.g. confidentiality) impacts the score more than a missing minor one (e.g. a boilerplate jurisdiction phrasing).
- **Evidence-first findings**: every result includes the matched snippet (or nearest paragraph, for semantic checks) so a reviewer can verify the finding in seconds rather than re-reading the whole document.

---

## 🛣️ Possible Extensions

- Swap the TF-IDF matcher for sentence-transformer embeddings for stronger semantic recall.
- Add a rule-authoring UI so non-technical compliance staff can add clauses without editing YAML.
- Batch-mode CLI for scanning an entire folder of contracts and producing a portfolio-level risk summary.
- Integrate an LLM call to draft suggested remedial language for each failed clause.

---

## License

MIT — see [LICENSE](LICENSE).
