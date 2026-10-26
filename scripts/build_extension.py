#!/usr/bin/env python3
"""
Driftless Extension Packager
Builds driftless-extension.zip from /extension directory for easy distribution.
"""
import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
EXT_DIR = ROOT_DIR / 'extension'
OUTPUT_ZIP = ROOT_DIR / 'driftless-extension.zip'

def build():
    print(f"Packaging Driftless Extension from: {EXT_DIR}")
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    files_added = 0
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in EXT_DIR.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                arcname = file_path.relative_to(EXT_DIR)
                zf.write(file_path, arcname)
                files_added += 1

    print(f"[OK] Created {OUTPUT_ZIP.name} ({files_added} files, {OUTPUT_ZIP.stat().st_size} bytes)")
    print("Ready to share with users to 'Load unpacked' in chrome://extensions!")

if __name__ == '__main__':
    build()
