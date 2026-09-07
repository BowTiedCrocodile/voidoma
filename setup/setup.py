#!/usr/bin/env python3
"""Install the desktop as the current user, optionally backing up existing files."""
import argparse
import datetime
import os
from pathlib import Path
import shutil
import sys

FILES = ('hyprland.lua', 'touchpad.lua', 'void-menu', 'menu.rasi', 'keys.txt', 'desktop-start',
         'workspace-status', 'audio-status', 'brightness', 'desktop-controls', 'display-menu', 'wallpaper.png', 'waybar.json',
         'waybar.css', 'mako.conf', 'hyprlock.conf', 'hypridle.conf', 'lock-screen',
         'screenshot', 'clipboard-menu', 'enable-idle.sh')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', action='store_true', help='back up existing configuration before replacing bundle files')
    parser.add_argument('--dry-run', action='store_true', help='show planned writes without changing files')
    args = parser.parse_args()
    if os.getuid() == 0:
        parser.error('Run as your desktop user, without sudo.')
    root = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))).absolute()
    source = Path(__file__).resolve().parents[1]
    def bundled(name):
        for directory in ('config', 'scripts', 'assets'):
            candidate = source / directory / name
            if candidate.is_file():
                return candidate
        parser.error(f'Missing bundled file: {name}')
    operations = [(bundled(name), root / 'hypr' / name) for name in FILES]
    operations.append((source / 'config/hyprland-portals.conf', root / 'xdg-desktop-portal/hyprland-portals.conf'))
    for name, example in [('10-wireplumber.conf', '/usr/share/examples/wireplumber/10-wireplumber.conf'),
                          ('20-pipewire-pulse.conf', '/usr/share/examples/pipewire/20-pipewire-pulse.conf')]:
        # Do not launch duplicate children when Void already configures them globally.
        system = Path('/etc/pipewire/pipewire.conf.d') / name
        target = root / 'pipewire/pipewire.conf.d' / name
        if not system.exists() and not target.exists():
            operations.append((Path(example), target))
    for src, dst in operations:
        if not src.is_file():
            parser.error(f'Missing {src}; run setup/install-deps.sh first.')
        if dst.is_symlink() or any(parent.is_symlink() for parent in dst.parents):
            parser.error(f'Refusing symlink destination: {dst}')
        if dst.exists() and not dst.is_file():
            parser.error(f'Destination is not a file: {dst}')
    existing = [dst for _, dst in operations if dst.exists()]
    if existing and not args.backup:
        parser.error('Configuration already exists. Use --backup to preserve it before replacement.')
    for src, dst in operations:
        print(f'{src.name} -> {dst}')
    if args.dry_run:
        return
    if existing:
        backup = root / ('void-desktop-backup-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        for name in ('hypr', 'pipewire', 'xdg-desktop-portal'):
            if (root / name).exists():
                shutil.copytree(root / name, backup / name, symlinks=True)
        print(f'Backup: {backup}')
    for src, dst in operations:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.name == 'hyprlock.conf' and dst.exists():
            old = dst.read_text()
            begin = '# BEGIN void-desktop fingerprint\n'
            end = '# END void-desktop fingerprint\n'
            if begin in old and end in old:
                block = old[old.index(begin):old.index(end) + len(end)]
                dst.write_text(src.read_text().rstrip() + '\n\n' + block)
                continue
        shutil.copy2(src, dst)
    print('Installed. See README.md for session startup and activation.')

if __name__ == '__main__':
    main()
