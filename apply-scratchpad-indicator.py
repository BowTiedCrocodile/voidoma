#!/usr/bin/env python3
"""Add the scratchpad indicator to an existing Waybar configuration."""
import argparse
import json
import os
from pathlib import Path
import shutil
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bundle', action='store_true')
args = parser.parse_args()
source = Path(__file__).resolve().parent
base = source if args.bundle else Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'hypr'
config = base / 'waybar.json'
css = base / 'waybar.css'
data = json.loads(config.read_text())
module = 'custom/scratchpad'
if module not in data['modules-left']:
    data['modules-left'].append(module)
data[module] = {
    'exec': 'python3 "${XDG_CONFIG_HOME:-$HOME/.config}/hypr/workspace-status" scratchpad',
    'return-type': 'json', 'restart-interval': 3, 'tooltip': True,
    'on-click': 'hyprctl dispatch \'hl.dsp.workspace.toggle_special("scratchpad")\''
}
style = '\n#custom-scratchpad { color: #a7c080; padding: 0 9px; font-size: 17px; }\n'
if not args.bundle:
    backup = base / ('backup-scratchpad-' + str(time.time_ns()))
    backup.mkdir()
    for name in ('waybar.json', 'waybar.css', 'workspace-status'):
        shutil.copy2(base / name, backup / name)
    shutil.copy2(source / 'workspace-status', base / 'workspace-status')
    print(f'Backup: {backup}')
config.write_text(json.dumps(data, indent=2) + '\n')
if '#custom-scratchpad' not in css.read_text():
    css.write_text(css.read_text() + style)
print('Scratchpad indicator installed.')
