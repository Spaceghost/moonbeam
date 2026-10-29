#!/usr/bin/env python3
"""Exercise import, separate settings, permissions, launcher, and repeat installs."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='moonlight-installer-') as directory:
    work = Path(directory)
    bundle, home = work / 'bundle', work / 'home with spaces'
    appdir = bundle / 'Moonbeam.AppDir'
    appdir.mkdir(parents=True)
    app = appdir / 'AppRun'
    app.write_text('#!/bin/sh\necho portable-launch-ok\n')
    app.chmod(0o755)
    (bundle / 'VERSION').write_text('test.1\n')
    shutil.copy2(root / 'scripts/install-moonbeam.sh', bundle / 'install.sh')
    original = home / '.var/app/com.moonlight_stream.Moonlight/config/Moonlight Game Streaming Project/Moonlight.conf'
    original.parent.mkdir(parents=True)
    saved = '[General]\nwidth=1280\nheight=720\nbitrate=10000\nkey=test-local-pairing\n\n[hosts]\nsize=1\n'
    original.write_text(saved)
    env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
               XDG_DATA_HOME=str(home / '.local/share'))
    for iteration in range(2):
        subprocess.run(['bash', str(bundle / 'install.sh')], check=True, env=env)
    target = home / '.config/Moonlight Game Streaming Project/Moonbeam.conf'
    text = target.read_text()
    for setting in ['width=1920', 'height=1080', 'fps=60', 'bitrate=30000',
                    'autoreconnect=true', 'key=test-local-pairing', '[hosts]\nsize=1']:
        assert setting in text, setting
    assert original.read_text() == saved
    assert target.stat().st_mode & 0o777 == 0o600
    launcher = home / '.local/bin/moonbeam'
    assert subprocess.check_output([str(launcher)], text=True).strip() == 'portable-launch-ok'
    target.write_text(text.replace('bitrate=30000', 'bitrate=25000'))
    subprocess.run(['bash', str(bundle / 'install.sh')], check=True, env=env)
    assert 'bitrate=25000' in target.read_text(), 'Updating must preserve edited settings'
    legacy = target.with_name('Moonlight Resilient.conf')
    target.rename(legacy)
    subprocess.run(['bash', str(bundle / 'install.sh')], check=True, env=env)
    assert 'bitrate=25000' in target.read_text(), 'Migration must preserve the previous fork settings'
    assert legacy.exists(), 'Migration must retain the original config'
    print('PASS: local-only pairing import, 1080p/60 defaults, permissions, paths with spaces, repeat install, user settings preserved')
