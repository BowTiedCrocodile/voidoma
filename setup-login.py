#!/usr/bin/env python3
"""Set a user's default LightDM session to Hyprland; run with sudo."""
import argparse
import datetime
import os
from pathlib import Path
import pwd
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('user')
parser.add_argument('--dry-run', action='store_true')
args = parser.parse_args()
account = pwd.getpwnam(args.user)
if account.pw_uid == 0:
    parser.error('Choose a normal desktop account.')
source = Path(__file__).resolve().parent / 'lightdm-session'
conf = Path('/etc/lightdm/lightdm.conf')
dmrc = Path(account.pw_dir) / '.dmrc'
wrapper = Path('/usr/local/bin/void-lightdm-session')
for path in (conf, Path('/usr/share/wayland-sessions/hyprland.desktop'), source):
    if not path.is_file():
        parser.error(f'Missing required file: {path}')
for path in (conf, dmrc, wrapper):
    if path.is_symlink():
        parser.error(f'Refusing symlink destination: {path}')
print(f'Set {args.user} session to hyprland; install {wrapper}; update {conf}.')
print('Login passwords and autologin user settings are unchanged. LightDM will not be restarted.')
if args.dry_run:
    raise SystemExit(0)
if os.getuid() != 0:
    parser.error('Run with sudo to update LightDM and AccountsService.')
backup = Path('/var/backups') / ('void-desktop-login-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
backup.mkdir(parents=True, mode=0o700)
for path in (conf, dmrc, wrapper):
    if path.exists():
        dest = backup / str(path).lstrip('/')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

def update(path, section, values):
    # Preserve existing comments and unrelated settings.
    lines = path.read_text().splitlines() if path.exists() else []
    start = next((i for i, line in enumerate(lines) if line.strip() == f'[{section}]'), None)
    if start is None:
        lines.extend(['', f'[{section}]'])
        start = len(lines) - 1
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip().startswith('[')), len(lines))
    for key, value in values.items():
        found = False
        for i in range(start + 1, end):
            line = lines[i].strip()
            if not line.startswith(('#', ';')) and line.split('=', 1)[0].strip() == key:
                lines[i] = f'{key}={value}'
                found = True
        if not found:
            lines.insert(end, f'{key}={value}')
            end += 1
    path.write_text('\n'.join(lines) + '\n')

wrapper.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(source, wrapper)
wrapper.chmod(0o755)
update(conf, 'Seat:*', {'user-session': 'hyprland', 'session-wrapper': str(wrapper)})
update(dmrc, 'Desktop', {'Session': 'hyprland'})
os.chown(dmrc, account.pw_uid, account.pw_gid)
dmrc.chmod(0o644)
# AccountsService preferences take precedence over .dmrc when it is running.
result = subprocess.run(['busctl', '--system', 'call', 'org.freedesktop.Accounts',
                         f'/org/freedesktop/Accounts/User{account.pw_uid}',
                         'org.freedesktop.Accounts.User', 'SetXSession', 's', 'hyprland'],
                        capture_output=True, text=True)
print(f'Backup: {backup}')
if result.returncode:
    print('AccountsService update failed; select Hyprland once at the greeter if needed:')
    print(result.stderr.strip())
subprocess.run(['lightdm', '--show-config'], check=True)
print('Ready for the next login. Choose XFCE in the greeter to return to it.')
