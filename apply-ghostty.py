#!/usr/bin/env python3
"""Use Ghostty for the desktop terminal shortcuts and menu."""
import os
from pathlib import Path
import shutil
import time

if not shutil.which('ghostty'):
    raise SystemExit('Install Ghostty first: sudo xbps-install ghostty')
base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'hypr'
for name in ('hyprland.lua', 'void-menu'):
    path = base / name
    original = path.read_text()
    updated = original.replace('hl.dsp.exec_cmd("alacritty")', 'hl.dsp.exec_cmd("ghostty")').replace('Terminal) exec alacritty ;;', 'Terminal) exec ghostty ;;')
    if updated != original:
        shutil.copy2(path, path.with_name(name + '.bak-' + str(time.time_ns())))
        path.write_text(updated)
print('Ghostty configured for Super+T, Super+Return, and the Terminal menu item.')
