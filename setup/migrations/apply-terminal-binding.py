#!/usr/bin/env python3
"""Set Super+T to terminal and Super+Shift+T to floating, preserving other settings."""
import argparse
import os
from pathlib import Path
import shutil
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bundle', action='store_true')
args = parser.parse_args()
base = Path(__file__).resolve().parents[2] / 'config' if args.bundle else Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'hypr'
replacements = {
    'hyprland.lua': [('bind("SUPER + T", "Toggle floating", hl.dsp.window.float({ action = "toggle" }))',
                      'bind("SUPER + T", "Terminal", hl.dsp.exec_cmd("ghostty"))\nbind("SUPER + SHIFT + T", "Toggle floating", hl.dsp.window.float({ action = "toggle" }))')],
    'keys.txt': [('Super + Return                Terminal', 'Super + T / Return            Terminal'),
                 ('Super + T                     Toggle floating', 'Super + Shift + T             Toggle floating')]
}
for name, changes in replacements.items():
    path = base / name
    original = path.read_text()
    text = original
    for old, new in changes:
        text = text.replace(old, new)
    if text != original:
        if not args.bundle:
            shutil.copy2(path, path.with_name(name + '.bak-' + str(time.time_ns())))
        path.write_text(text)
print('Terminal and floating shortcuts updated.')
