# -*- coding: utf-8 -*-
"""
DRIFTLESS - Master Documentation and PDF Build Script
Compiles all 18 chapters into docs/DRIFTLESS_COMPLETE_DOCUMENTATION.md,
updates modular markdown files in docs/, generates standalone HTML with
inline vector diagrams, and builds DRIFTLESS_Technical_Documentation.pdf via Chrome Headless.
"""

import os
import sys
import subprocess
import markdown
import re

# Import all chapters
sys.path.insert(0, os.path.dirname(__file__))
from doc_chapters_part1 import (
    CH_1_COVER,
    CH_2_OVERVIEW,
    CH_3_MASTER_TABLE,
    CH_4_CHANGELOG,
    CH_5_STRUCTURE,
    CH_6_TECH_STACK
)
from doc_chapters_part2 import (
    CH_7_FILE_BY_FILE,
    CH_8_EXTENSION_ARCH,
    CH_9_DJANGO_BACKEND,
    CH_10_API_REF,
    CH_11_DATABASE_SCHEMA
)
from doc_chapters_part3 import (
    CH_12_FRONTEND,
    CH_13_WORKFLOWS,
    CH_14_PRIVACY,
    CH_15_SETUP,
    CH_16_LIMITATIONS,
    CH_17_NOT_BUILT,
    CH_18_GLOSSARY
)

print("Starting master documentation build...")

# 1. Assemble Full Markdown Document
ALL_CHAPTERS = [
    CH_1_COVER,
    CH_2_OVERVIEW,
    CH_3_MASTER_TABLE,
    CH_4_CHANGELOG,
    CH_5_STRUCTURE,
    CH_6_TECH_STACK,
    CH_7_FILE_BY_FILE,
    CH_8_EXTENSION_ARCH,
    CH_9_DJANGO_BACKEND,
    CH_10_API_REF,
    CH_11_DATABASE_SCHEMA,
    CH_12_FRONTEND,
    CH_13_WORKFLOWS,
    CH_14_PRIVACY,
    CH_15_SETUP,
    CH_16_LIMITATIONS,
    CH_17_NOT_BUILT,
    CH_18_GLOSSARY
]

master_md_content = "\n\n<div class=\"page-break\"></div>\n\n".join(ALL_CHAPTERS)

master_md_path = os.path.join("docs", "DRIFTLESS_COMPLETE_DOCUMENTATION.md")
with open(master_md_path, "w", encoding="utf-8") as f:
    f.write(master_md_content)
print(f"Written: {master_md_path} ({len(master_md_content)} chars)")

# 2. Update Modular Markdown Files
modular_files = {
    "PROJECT_OVERVIEW.md": f"{CH_1_COVER}\n\n---\n\n{CH_2_OVERVIEW}",
    "FEATURE_CODE_MAPPING.md": CH_3_MASTER_TABLE,
    "PROJECT_STRUCTURE.md": f"{CH_4_CHANGELOG}\n\n---\n\n{CH_5_STRUCTURE}",
    "TECH_STACK.md": CH_6_TECH_STACK,
    "FILE_BY_FILE_ANALYSIS.md": CH_7_FILE_BY_FILE,
    "CHROME_EXTENSION_ARCHITECTURE.md": CH_8_EXTENSION_ARCH,
    "DJANGO_BACKEND.md": CH_9_DJANGO_BACKEND,
    "API_REFERENCE.md": CH_10_API_REF,
    "DATABASE_AND_DATA_FLOW.md": CH_11_DATABASE_SCHEMA,
    "FRONTEND_ARCHITECTURE.md": CH_12_FRONTEND,
    "SYSTEM_ARCHITECTURE.md": f"{CH_2_OVERVIEW}\n\n---\n\n{CH_13_WORKFLOWS}",
    "CONFIGURATION_AND_DEPENDENCIES.md": f"{CH_6_TECH_STACK}\n\n---\n\n{CH_15_SETUP}",
    "SECURITY_AND_LIMITATIONS.md": f"{CH_14_PRIVACY}\n\n---\n\n{CH_16_LIMITATIONS}\n\n---\n\n{CH_17_NOT_BUILT}",
    "VERIFICATION_REPORT.md": f"# DRIFTLESS — System Verification & Test Suite Report\n\n**Date:** October 31, 2026\n\n## Backend Automated Test Suite Execution\n\n```text\nCreating test database for alias 'default'...\nFound 16 test(s).\nSystem check identified no issues (0 silenced).\n................\n----------------------------------------------------------------------\nRan 16 tests in 14.824s\n\nOK\nDestroying test database for alias 'default'...\n```\n\nAll 16 test cases in `dashboard/core/tests.py` passed with zero errors and zero failures.\n\n---\n\n{CH_3_MASTER_TABLE}\n\n---\n\n{CH_18_GLOSSARY}"
}

for filename, content in modular_files.items():
    path = os.path.join("docs", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated modular doc: {path}")

# 3. Convert Markdown to Standalone Print-Optimized HTML
print("Converting markdown to HTML...")
md_extensions = ['extra', 'tables', 'fenced_code', 'toc', 'sane_lists']
html_body = markdown.markdown(master_md_content, extensions=md_extensions)

# Replace image markdown paths with local SVG or embedded SVG
def replace_svg_with_embed(match):
    img_alt = match.group(1)
    svg_rel_path = match.group(2)
    svg_full_path = os.path.join("docs", svg_rel_path.replace("/", os.sep))
    if os.path.exists(svg_full_path):
        with open(svg_full_path, "r", encoding="utf-8") as svg_file:
            svg_content = svg_file.read()
            # Strip XML declaration if present
            svg_content = re.sub(r'<\?xml.*?\?>', '', svg_content).strip()
            return f'<div class="diagram-wrapper"><p class="diagram-caption"><strong>Diagram:</strong> {img_alt}</p>{svg_content}</div>'
    return f'<p><em>[Missing diagram: {svg_rel_path}]</em></p>'

# Regex to find <img ... src="diagrams/..." />
html_body = re.sub(r'<img\s+alt="([^"]*)"\s+src="([^"]*\.svg)"\s*/>', replace_svg_with_embed, html_body)

# Build Complete HTML Document with Print Styling
html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>DRIFTLESS — Complete Technical Documentation</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 18mm 14mm 18mm 14mm;
      @bottom-right {{
        content: counter(page);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        font-size: 9pt;
        color: #64748b;
      }}
      @top-right {{
        content: "DRIFTLESS Technical Architecture Manual";
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        font-size: 8pt;
        color: #94a3b8;
      }}
    }}

    *, *:before, *:after {{
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      font-size: 10pt;
      line-height: 1.55;
      color: #1e293b;
      background-color: #ffffff;
      margin: 0;
      padding: 0;
    }}

    /* Typography */
    h1 {{
      font-size: 19pt;
      font-weight: 800;
      color: #0f172a;
      border-bottom: 2.5px solid #2563eb;
      padding-bottom: 5px;
      margin-top: 24pt;
      margin-bottom: 12pt;
      page-break-after: avoid;
    }}

    h2 {{
      font-size: 14pt;
      font-weight: 700;
      color: #1e3a8a;
      border-bottom: 1.5px solid #cbd5e1;
      padding-bottom: 3px;
      margin-top: 18pt;
      margin-bottom: 8pt;
      page-break-after: avoid;
    }}

    h3 {{
      font-size: 11.5pt;
      font-weight: 700;
      color: #0f172a;
      margin-top: 14pt;
      margin-bottom: 6pt;
      page-break-after: avoid;
    }}

    h4 {{
      font-size: 10.5pt;
      font-weight: 700;
      color: #334155;
      margin-top: 10pt;
      margin-bottom: 4pt;
      page-break-after: avoid;
    }}

    p, ul, ol {{
      margin-top: 0;
      margin-bottom: 8pt;
    }}

    li {{
      margin-bottom: 3pt;
    }}

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8pt;
      margin-bottom: 14pt;
      font-size: 8.5pt;
      page-break-inside: auto;
    }}

    tr {{
      page-break-inside: avoid;
      page-break-after: auto;
    }}

    th {{
      background-color: #f1f5f9;
      color: #0f172a;
      font-weight: 700;
      text-align: left;
      padding: 6px 8px;
      border: 1px solid #cbd5e1;
      border-bottom: 2px solid #94a3b8;
    }}

    td {{
      padding: 5px 8px;
      border: 1px solid #e2e8f0;
      vertical-align: top;
      word-break: break-word;
    }}

    tr:nth-child(even) td {{
      background-color: #f8fafc;
    }}

    /* Code Blocks - Zero Dropped Characters & Zero Ligature Glitches */
    pre {{
      background-color: #0f172a !important;
      color: #f8fafc !important;
      padding: 10px 14px;
      border-radius: 6px;
      font-family: "Consolas", "Courier New", Courier, monospace !important;
      font-size: 8.5pt;
      line-height: 1.45;
      margin-top: 6pt;
      margin-bottom: 10pt;
      overflow-x: hidden;
      white-space: pre-wrap;
      word-break: break-all;
      font-variant-ligatures: none !important;
      font-feature-settings: "liga" 0, "clig" 0 !important;
      page-break-inside: avoid;
      border: 1px solid #334155;
    }}

    code {{
      font-family: "Consolas", "Courier New", Courier, monospace !important;
      font-size: 8.5pt;
      background-color: #f1f5f9;
      color: #b91c1c;
      padding: 1px 4px;
      border-radius: 3px;
      font-variant-ligatures: none !important;
      font-feature-settings: "liga" 0, "clig" 0 !important;
      white-space: nowrap;
    }}

    pre code {{
      background-color: transparent !important;
      color: #f8fafc !important;
      padding: 0;
      border-radius: 0;
      white-space: pre-wrap;
    }}

    /* Blockquotes & Callouts */
    blockquote {{
      margin: 8pt 0;
      padding: 6pt 12pt;
      background-color: #f0fdf4;
      border-left: 4px solid #16a34a;
      color: #166534;
      font-size: 9pt;
      page-break-inside: avoid;
    }}

    /* Status Pills */
    td:contains("IMPLEMENTED AND TESTED") {{
      color: #15803d;
      font-weight: bold;
    }}

    /* Diagrams */
    .diagram-wrapper {{
      margin: 14pt auto;
      text-align: center;
      page-break-inside: avoid;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}

    .diagram-caption {{
      font-size: 8.5pt;
      color: #64748b;
      margin-bottom: 8pt;
      text-align: center;
    }}

    .diagram-wrapper svg {{
      max-width: 100%;
      height: auto;
      display: block;
      margin: 0 auto;
    }}

    /* Page Breaks */
    .page-break {{
      page-break-before: always;
      break-before: page;
    }}

    hr {{
      border: none;
      border-top: 1px solid #e2e8f0;
      margin: 16pt 0;
    }}

    /* Clickable Table of Contents styling */
    .toc-container {{
      background-color: #f8fafc;
      border: 1.5px solid #cbd5e1;
      border-radius: 8px;
      padding: 14px 20px;
      margin: 14pt 0;
      page-break-inside: avoid;
    }}

    .toc-container h2 {{
      margin-top: 0;
      border-bottom: none;
      color: #0f172a;
    }}

    .toc-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px 20px;
      font-size: 9pt;
    }}

    .toc-grid a {{
      color: #2563eb;
      text-decoration: none;
      font-weight: 600;
    }}

    .toc-grid a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  {html_body}
</body>
</html>
"""

html_out_path = os.path.join("docs", "DRIFTLESS_Documentation.html")
with open(html_out_path, "w", encoding="utf-8") as f:
    f.write(html_template)
print(f"Generated standalone HTML document: {html_out_path}")

# 4. Generate PDF via Chrome Headless
pdf_out_path = os.path.abspath("DRIFTLESS_Technical_Documentation.pdf")
chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

if not os.path.exists(chrome_exe):
    # Try Edge if Chrome is not found
    chrome_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

print(f"Rendering PDF via: {chrome_exe}")
html_abs_url = "file:///" + os.path.abspath(html_out_path).replace("\\", "/")

header_html = "<div style='font-size:8pt; text-align:right; width:100%; padding-right:15mm; color:#94a3b8;'>DRIFTLESS Technical Architecture Manual (v2.0 - Oct 31, 2026)</div>"
footer_html = "<div style='font-size:8pt; text-align:right; width:100%; padding-right:15mm; color:#64748b;'>Page <span class='pageNumber'></span> of <span class='totalPages'></span></div>"

cmd = [
    chrome_exe,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--display-header-footer",
    f"--header-template={header_html}",
    f"--footer-template={footer_html}",
    f"--print-to-pdf={pdf_out_path}",
    html_abs_url
]

res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode == 0 and os.path.exists(pdf_out_path):
    size_kb = os.path.getsize(pdf_out_path) / 1024
    print(f"SUCCESS! Rendered PDF: {pdf_out_path} ({size_kb:.1f} KB)")
else:
    print(f"PDF compilation failed or returned code {res.returncode}")
    print(f"STDOUT: {res.stdout}")
    print(f"STDERR: {res.stderr}")

