#!/usr/bin/env python3
"""Emit one shared artifact version and an upgrade-safe native installer version."""
from pathlib import Path
import subprocess
import json
from release_common import native_version

root = Path(__file__).resolve().parents[1]
base = (root / 'app/moonbeam-version.txt').read_text().strip()
commit = (subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
          if (root / '.git').exists() else json.loads((root / 'SOURCE_MANIFEST.json').read_text())['commit'])
print(f'version={base}')
print(f'native_version={native_version(base)}')
