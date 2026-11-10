#!/usr/bin/env python3
"""Emit one shared artifact version and an upgrade-safe native installer version."""
from pathlib import Path
from release_common import native_version, upstream_release

root = Path(__file__).resolve().parents[1]
base = (root / 'app/moonbeam-version.txt').read_text().strip()
upstream_release(root)
print(f'version={base}')
print(f'native_version={native_version(base)}')
