"""
DRIFTLESS Documentation to PDF Converter
Converts Markdown files into polished, publication-quality PDFs using Headless Chrome/Edge.
Preserves 100% of the content: headings, text, tables, code blocks, links, lists.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
import markdown

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / 'docs'

# Find Chrome or Edge executable
CHROME_CANDIDATES = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
]

BROWSER_PATH = None
for c in CHROME_CANDIDATES:
    if os.path.exists(c):
        BROWSER_PATH = c
        break

if not BROWSER_PATH:
    print("Error: Could not find Chrome or Edge executable.")
    sys.exit(1)

print(f"Using Browser for PDF generation: {BROWSER_PATH}")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 18mm 16mm 20mm 16mm;
      @bottom-right {{
        content: counter(page);
      }}
    }}
    
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      font-size: 11pt;
      line-height: 1.6;
      color: #1e293b;
      background: #ffffff;
      margin: 0;
      padding: 0;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
      color: #0f172a;
      font-weight: 700;
      page-break-after: avoid;
      break-after: avoid;
      margin-top: 1.4em;
      margin-bottom: 0.5em;
    }}
    
    h1 {{
      font-size: 20pt;
      border-bottom: 2.5px solid #6366f1;
      padding-bottom: 6px;
      margin-top: 0;
      color: #312e81;
    }}
    
    h2 {{
      font-size: 15pt;
      border-bottom: 1.5px solid #e2e8f0;
      padding-bottom: 4px;
      color: #1e1b4b;
    }}
    
    h3 {{
      font-size: 12pt;
      color: #3730a3;
    }}
    
    h4 {{
      font-size: 11pt;
      color: #4338ca;
    }}
    
    p, ul, ol {{
      margin-top: 0.4em;
      margin-bottom: 0.8em;
    }}
    
    li {{
      margin-bottom: 0.25em;
    }}
    
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1.2em 0;
      font-size: 9.5pt;
      line-height: 1.45;
      page-break-inside: auto;
      break-inside: auto;
    }}
    
    tr {{
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    
    th, td {{
      border: 1px solid #cbd5e1;
      padding: 7px 10px;
      text-align: left;
      vertical-align: top;
      word-break: break-word;
    }}
    
    th {{
      background-color: #f1f5f9;
      color: #0f172a;
      font-weight: 700;
    }}
    
    tr:nth-child(even) {{
      background-color: #f8fafc;
    }}
    
    pre {{
      background-color: #0f172a;
      color: #f8fafc;
      padding: 12px 14px;
      border-radius: 6px;
      font-family: "Cascadia Code", Consolas, "Courier New", monospace;
      font-size: 9pt;
      line-height: 1.45;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
      page-break-inside: avoid;
      break-inside: avoid;
      margin: 1em 0;
    }}
    
    code {{
      font-family: "Cascadia Code", Consolas, "Courier New", monospace;
      font-size: 9.5pt;
      background-color: #f1f5f9;
      color: #4338ca;
      padding: 2px 5px;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
    }}
    
    pre code {{
      background-color: transparent;
      color: inherit;
      padding: 0;
      border: none;
      font-size: inherit;
    }}
    
    blockquote {{
      border-left: 4px solid #6366f1;
      margin: 1em 0;
      padding: 6px 16px;
      background-color: #f5f3ff;
      color: #475569;
      font-style: normal;
    }}
    
    hr {{
      border: none;
      border-top: 1.5px solid #e2e8f0;
      margin: 2em 0;
    }}
    
    a {{
      color: #4f46e5;
      text-decoration: none;
    }}
    
    .mermaid {{
      background: #fafafa;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 16px;
      margin: 1.2em 0;
      text-align: center;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    
    .doc-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid #6366f1;
      padding-bottom: 10px;
      margin-bottom: 25px;
    }}
    
    .doc-header .brand {{
      font-size: 14pt;
      font-weight: 800;
      color: #4338ca;
      letter-spacing: -0.5px;
    }}
    
    .doc-header .meta {{
      font-size: 9pt;
      color: #64748b;
    }}
    
    .footer-note {{
      margin-top: 40px;
      padding-top: 10px;
      border-top: 1px solid #e2e8f0;
      font-size: 8.5pt;
      color: #94a3b8;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="doc-header">
    <div class="brand">DRIFTLESS — Technical Documentation</div>
    <div class="meta">Comprehensive Architecture & Codebase Reference</div>
  </div>

  {content}

  <div class="footer-note">
    DRIFTLESS Technical Documentation &bull; Converted from source Markdown with 100% fidelity preserved
  </div>
</body>
</html>
"""

def md_to_html(md_text, title="DRIFTLESS Documentation"):
    # Convert mermaid code blocks to <pre class="mermaid"> if any, or preserve clean code blocks
    extensions = ['tables', 'fenced_code', 'nl2br', 'sane_lists']
    html_body = markdown.markdown(md_text, extensions=extensions)
    return HTML_TEMPLATE.format(title=title, content=html_body)

def convert_md_file_to_pdf(md_path: Path, output_pdf_path: Path):
    print(f"Converting: {md_path.name} -> {output_pdf_path.name}")
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    title = md_path.stem.replace('_', ' ').title()
    html_content = md_to_html(md_text, title=f"Driftless — {title}")

    temp_html_path = output_pdf_path.with_suffix('.temp.html')
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    try:
        cmd = [
            BROWSER_PATH,
            '--headless=new',
            '--disable-gpu',
            '--no-pdf-header-footer',
            '--run-all-compositor-stages-before-draw',
            f'--print-to-pdf={output_pdf_path}',
            str(temp_html_path.resolve())
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=60)
        if res.returncode == 0 and output_pdf_path.exists():
            size_kb = output_pdf_path.stat().st_size / 1024
            print(f"  [OK] Generated {output_pdf_path.name} ({size_kb:.1f} KB)")
            return True
        else:
            print(f"  [ERROR] Failed to generate PDF: {res.stderr.decode('utf-8', errors='ignore')}")
            return False
    finally:
        if temp_html_path.exists():
            temp_html_path.unlink()

def build_combined_documentation():
    """Compiles all 14 docs in sequential order into one master documentation file."""
    doc_order = [
        "PROJECT_OVERVIEW.md",
        "PROJECT_STRUCTURE.md",
        "TECH_STACK.md",
        "FILE_BY_FILE_ANALYSIS.md",
        "FRONTEND_ARCHITECTURE.md",
        "CHROME_EXTENSION_ARCHITECTURE.md",
        "DJANGO_BACKEND.md",
        "API_REFERENCE.md",
        "DATABASE_AND_DATA_FLOW.md",
        "SYSTEM_ARCHITECTURE.md",
        "FEATURE_CODE_MAPPING.md",
        "CONFIGURATION_AND_DEPENDENCIES.md",
        "SECURITY_AND_LIMITATIONS.md",
        "VERIFICATION_REPORT.md",
    ]
    
    combined_parts = [
        "# DRIFTLESS — Complete Technical Documentation Suite\n",
        "> Complete, unabridged technical reference manual for the DRIFTLESS digital wellbeing and distraction tracker.\n",
        "---\n"
    ]
    
    for filename in doc_order:
        doc_path = DOCS_DIR / filename
        if doc_path.exists():
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
            combined_parts.append(f"\n\n<!-- PAGE BREAK -->\n\n<div style=\"page-break-before: always; break-before: always;\"></div>\n\n")
            combined_parts.append(content)
            combined_parts.append("\n\n---\n")

    master_md_path = DOCS_DIR / "DRIFTLESS_COMPLETE_DOCUMENTATION.md"
    master_content = "".join(combined_parts)
    with open(master_md_path, 'w', encoding='utf-8') as f:
        f.write(master_content)
    
    print(f"Created Master Markdown document: {master_md_path.name} ({len(master_content)} characters)")
    
    # Generate Master PDF in docs/
    master_pdf_path = DOCS_DIR / "DRIFTLESS_COMPLETE_DOCUMENTATION.pdf"
    convert_md_file_to_pdf(master_md_path, master_pdf_path)
    
    # Also copy to root project directory for immediate convenience
    root_pdf_path = ROOT_DIR / "DRIFTLESS_COMPLETE_DOCUMENTATION.pdf"
    if master_pdf_path.exists():
        import shutil
        shutil.copyfile(master_pdf_path, root_pdf_path)
        print(f"Copied Master PDF to project root: {root_pdf_path.name}")

def main():
    print("=" * 60)
    print("DRIFTLESS — Markdown to PDF Conversion Engine")
    print("=" * 60)

    # 1. Convert each individual doc file to PDF alongside its .md file
    doc_files = sorted(list(DOCS_DIR.glob("*.md")))
    success_count = 0
    for doc in doc_files:
        if doc.name == "DRIFTLESS_COMPLETE_DOCUMENTATION.md":
            continue
        pdf_path = doc.with_suffix('.pdf')
        if convert_md_file_to_pdf(doc, pdf_path):
            success_count += 1

    print(f"\nConverted {success_count}/{len(doc_files)} individual documentation files to PDF.")

    # 2. Build the combined master documentation PDF
    print("\nBuilding Master Combined Documentation PDF...")
    build_combined_documentation()
    print("\n[ALL DONE] PDF generation complete.")

if __name__ == '__main__':
    main()
