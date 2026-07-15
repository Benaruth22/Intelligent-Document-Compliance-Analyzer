"""
app.py
------
Streamlit dashboard for the Intelligent Document Compliance Analyzer.

Run with:
    streamlit run app.py
"""

import os
import tempfile

import pandas as pd
import streamlit as st

from src.compliance_analyzer import ComplianceAnalyzer
from src.report_generator import save_html, save_pdf

st.set_page_config(page_title="Document Compliance Analyzer", page_icon="📋", layout="wide")

RULES_PATH = "rules/compliance_rules.yaml"

STATUS_EMOJI = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌"}


@st.cache_resource
def get_analyzer(rules_path: str):
    return ComplianceAnalyzer(rules_path)


def main():
    st.title("📋 Intelligent Document Compliance Analyzer")
    st.caption(
        "Upload a contract, policy, or agreement and instantly check it against "
        "a configurable set of compliance rules — data privacy, security, "
        "financial, and contractual clauses."
    )

    with st.sidebar:
        st.header("Settings")
        rules_file = st.text_input("Rules file", value=RULES_PATH)
        st.markdown("---")
        st.markdown(
            "**Rule categories included:**\n"
            "- Data Privacy\n- Security\n- Contract Terms\n"
            "- Financial Compliance\n- Liability\n- Accessibility"
        )

    uploaded = st.file_uploader("Upload a document", type=["pdf", "docx", "txt"])

    if uploaded is None:
        st.info("Upload a .pdf, .docx, or .txt file to begin analysis, or try the bundled sample.")
        if st.button("Analyze bundled sample contract"):
            uploaded = open("sample_docs/sample_contract.txt", "rb")
            uploaded.name = "sample_contract.txt"
        else:
            return

    suffix = os.path.splitext(uploaded.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    analyzer = get_analyzer(rules_file)
    with st.spinner("Analyzing document..."):
        report = analyzer.analyze_file(tmp_path)

    score = report.overall_score
    color = "green" if score >= 80 else "orange" if score >= 50 else "red"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Score", f"{score}%")
    col2.metric("Passed", report.passed)
    col3.metric("Warnings", report.warnings)
    col4.metric("Failed", report.failed)

    st.markdown(f"### Overall Compliance: :{color}[{score}%]")
    st.progress(min(int(score), 100) / 100)

    st.subheader("Compliance by Category")
    cat_df = pd.DataFrame(
        [{"Category": k, "Score": v} for k, v in report.category_scores.items()]
    ).sort_values("Score", ascending=False)
    st.bar_chart(cat_df.set_index("Category"))

    st.subheader("Detailed Findings")
    for f in report.findings:
        emoji = STATUS_EMOJI[f["status"]]
        with st.expander(f"{emoji} [{f['severity'].upper()}] {f['id']} — {f['title']}"):
            st.write(f["description"])
            st.caption(f"Category: {f['category']} | Status: {f['status']} | Confidence: {f['confidence']}")
            st.code(f["evidence"] or "No evidence captured.", language=None)

    st.markdown("---")
    st.subheader("Export Report")
    ecol1, ecol2 = st.columns(2)
    html_path = save_html(report, tmp_path + "_report.html")
    with open(html_path, "rb") as f:
        ecol1.download_button("Download HTML Report", f, file_name="compliance_report.html")

    try:
        pdf_path = save_pdf(report, tmp_path + "_report.pdf")
        with open(pdf_path, "rb") as f:
            ecol2.download_button("Download PDF Report", f, file_name="compliance_report.pdf")
    except Exception as e:
        ecol2.warning(f"PDF export unavailable: {e}")


if __name__ == "__main__":
    main()
