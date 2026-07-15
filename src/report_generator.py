"""
report_generator.py
--------------------
Renders a ComplianceReport as JSON, HTML (styled, shareable), or PDF.
"""

from __future__ import annotations

import json
import os
from .compliance_analyzer import ComplianceReport

STATUS_COLORS = {
    "PASS": "#1e8e3e",
    "WARNING": "#e8a300",
    "FAIL": "#d93025",
}

SEVERITY_BADGE = {
    "critical": "#d93025",
    "major": "#e8a300",
    "minor": "#5f6368",
}


def save_json(report: ComplianceReport, out_path: str) -> str:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)
    return out_path


def _score_color(score: float) -> str:
    if score >= 80:
        return "#1e8e3e"
    if score >= 50:
        return "#e8a300"
    return "#d93025"


def render_html(report: ComplianceReport) -> str:
    findings_rows = ""
    for f in report.findings:
        color = STATUS_COLORS[f["status"]]
        sev_color = SEVERITY_BADGE[f["severity"]]
        confidence = f"{f['confidence']:.2f}" if f["confidence"] else "—"
        findings_rows += f"""
        <tr>
            <td class="mono">{f['id']}</td>
            <td>{f['title']}<div class="desc">{f['description']}</div></td>
            <td>{f['category']}</td>
            <td><span class="badge" style="background:{sev_color}">{f['severity'].upper()}</span></td>
            <td><span class="badge" style="background:{color}">{f['status']}</span></td>
            <td class="mono">{confidence}</td>
            <td class="evidence">{f['evidence'] or '—'}</td>
        </tr>"""

    category_bars = ""
    for cat, score in sorted(report.category_scores.items(), key=lambda x: -x[1]):
        category_bars += f"""
        <div class="cat-row">
            <div class="cat-label">{cat}</div>
            <div class="cat-bar-track">
                <div class="cat-bar-fill" style="width:{score}%; background:{_score_color(score)}"></div>
            </div>
            <div class="cat-score">{score}%</div>
        </div>"""

    overall_color = _score_color(report.overall_score)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Compliance Report — {report.filename}</title>
<style>
    :root {{
        --bg: #0f1115;
        --card: #ffffff;
        --text: #1f2328;
        --muted: #5f6368;
        --border: #e5e7eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
        background: #f4f5f7;
        color: var(--text);
        margin: 0;
        padding: 40px 20px;
    }}
    .container {{ max-width: 1000px; margin: 0 auto; }}
    .header {{
        background: linear-gradient(135deg, #1a1c23, #2b2f3a);
        color: white;
        border-radius: 14px;
        padding: 32px 36px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 20px;
    }}
    .header h1 {{ margin: 0 0 6px 0; font-size: 22px; font-weight: 600; }}
    .header .sub {{ color: #9aa0a6; font-size: 13px; }}
    .score-circle {{
        width: 110px; height: 110px; border-radius: 50%;
        border: 8px solid {overall_color};
        display: flex; align-items: center; justify-content: center;
        font-size: 28px; font-weight: 700; color: {overall_color};
        background: rgba(255,255,255,0.05);
    }}
    .summary-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 24px;
    }}
    .stat-card {{
        background: var(--card); border: 1px solid var(--border);
        border-radius: 10px; padding: 16px; text-align: center;
    }}
    .stat-card .num {{ font-size: 24px; font-weight: 700; }}
    .stat-card .label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }}
    .card {{
        background: var(--card); border: 1px solid var(--border);
        border-radius: 12px; padding: 24px; margin-bottom: 24px;
    }}
    .card h2 {{ font-size: 16px; margin-top: 0; }}
    .cat-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
    .cat-label {{ width: 180px; font-size: 13px; color: var(--muted); }}
    .cat-bar-track {{ flex: 1; height: 10px; background: #eef0f2; border-radius: 6px; overflow: hidden; }}
    .cat-bar-fill {{ height: 100%; border-radius: 6px; }}
    .cat-score {{ width: 48px; text-align: right; font-size: 13px; font-weight: 600; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{ text-align: left; padding: 10px 8px; border-bottom: 2px solid var(--border); color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: .03em; }}
    td {{ padding: 12px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }}
    .mono {{ font-family: 'SF Mono', Consolas, monospace; font-size: 12px; color: var(--muted); }}
    .desc {{ color: var(--muted); font-size: 12px; margin-top: 3px; }}
    .evidence {{ color: #333; font-style: italic; font-size: 12px; max-width: 260px; }}
    .badge {{
        color: white; padding: 3px 9px; border-radius: 20px;
        font-size: 11px; font-weight: 600; white-space: nowrap;
    }}
    .footer {{ text-align: center; color: var(--muted); font-size: 12px; margin-top: 30px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <h1>Intelligent Document Compliance Analyzer</h1>
            <div class="sub">File: {report.filename} &middot; Generated: {report.generated_at}</div>
        </div>
        <div class="score-circle">{report.overall_score}%</div>
    </div>

    <div class="summary-grid">
        <div class="stat-card"><div class="num">{report.total_rules}</div><div class="label">Rules Checked</div></div>
        <div class="stat-card"><div class="num" style="color:#1e8e3e">{report.passed}</div><div class="label">Passed</div></div>
        <div class="stat-card"><div class="num" style="color:#e8a300">{report.warnings}</div><div class="label">Warnings</div></div>
        <div class="stat-card"><div class="num" style="color:#d93025">{report.failed}</div><div class="label">Failed</div></div>
    </div>

    <div class="card">
        <h2>Compliance by Category</h2>
        {category_bars}
    </div>

    <div class="card">
        <h2>Detailed Findings</h2>
        <table>
            <thead>
                <tr>
                    <th>Rule ID</th><th>Requirement</th><th>Category</th>
                    <th>Severity</th><th>Status</th><th>Confidence</th><th>Evidence</th>
                </tr>
            </thead>
            <tbody>
                {findings_rows}
            </tbody>
        </table>
    </div>

    <div class="footer">Generated by Intelligent Document Compliance Analyzer</div>
</div>
</body>
</html>"""
    return html


def save_html(report: ComplianceReport, out_path: str) -> str:
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(render_html(report))
    return out_path


def save_pdf(report: ComplianceReport, out_path: str) -> str:
    """
    Renders the report as a PDF using reportlab (no external browser/engine
    dependency required, so it works in constrained/offline environments).
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=18)
    normal = styles["Normal"]
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=10)

    doc = SimpleDocTemplate(out_path, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    story = []

    story.append(Paragraph("Intelligent Document Compliance Analyzer", title_style))
    story.append(Paragraph(f"File: {report.filename}", normal))
    story.append(Paragraph(f"Generated: {report.generated_at}", normal))
    story.append(Paragraph(f"Overall Compliance Score: <b>{report.overall_score}%</b>", normal))
    story.append(Spacer(1, 14))

    summary_data = [["Total Rules", "Passed", "Warnings", "Failed"],
                     [report.total_rules, report.passed, report.warnings, report.failed]]
    summary_table = Table(summary_data, hAlign="LEFT")
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2f3a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 18))

    story.append(Paragraph("Detailed Findings", styles["Heading2"]))
    table_data = [["ID", "Requirement", "Severity", "Status", "Evidence"]]
    for f in report.findings:
        table_data.append([
            f["id"],
            Paragraph(f["title"], small),
            f["severity"],
            f["status"],
            Paragraph((f["evidence"] or "-")[:180], small),
        ])

    findings_table = Table(table_data, colWidths=[0.55 * inch, 1.6 * inch, 0.7 * inch, 0.7 * inch, 2.6 * inch])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2f3a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    status_colors = {"PASS": colors.HexColor("#1e8e3e"), "WARNING": colors.HexColor("#e8a300"),
                      "FAIL": colors.HexColor("#d93025")}
    for i, f in enumerate(report.findings, start=1):
        style_cmds.append(("TEXTCOLOR", (3, i), (3, i), status_colors[f["status"]]))
    findings_table.setStyle(TableStyle(style_cmds))
    story.append(findings_table)

    doc.build(story)
    return out_path
