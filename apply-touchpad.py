#!/usr/bin/env python3
"""Install the agreed touchpad gesture map, backing up existing user settings."""
import argparse
import os
from pathlib import Path
import shutil
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bundle', action='store_true')
args = parser.parse_args()
source = Path(__file__).resolve().parent
base = source if args.bundle else Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'hypr'
config = base / 'hyprland.lua'
keys = base / 'keys.txt'
line = 'dofile(base .. "touchpad.lua")'
if not args.bundle:
    backup = base / ('backup-touchpad-' + str(time.time_ns()))
    backup.mkdir()
    for name in ('hyprland.lua', 'keys.txt', 'touchpad.lua'):
        if (base / name).exists():
            shutil.copy2(base / name, backup / name)
    shutil.copy2(source / 'touchpad.lua', base / 'touchpad.lua')
    print(f'Backup: {backup}')
if line not in config.read_text():
    config.write_text(config.read_text().rstrip() + '\n\n' + line + '\n')
if 'Touchpad gestures' not in keys.read_text():
    keys.write_text(keys.read_text().rstrip() + '''

Touchpad gestures
One-finger tap                Left click
Two-finger tap / press        Right click
Two-finger scroll             Natural scrolling
Pinch                         Application zoom where supported
Three-finger left / right     Switch numbered workspace
Three-finger up               Applications
Three-finger down             Toggle scratchpad
Four-finger up                Toggle fullscreen
''')
print('Touchpad configuration installed.')

keys.write_text(keys.read_text().replace("Two-finger tap                Right click", "Two-finger tap / press        Right click"))
