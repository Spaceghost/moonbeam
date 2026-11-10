#!/usr/bin/env python3
"""Emit one shared artifact version and an upgrade-safe native installer version."""
from pathlib import Path
import subprocess
from release_common import native_version

root = Path(__file__).resolve().parents[1]
base = (root / 'app/moonbeam-version.txt').read_text().strip()
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
print(f'version={base}+g{commit[:12]}')
print(f'native_version={native_version(base)}')
