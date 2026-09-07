#!/usr/bin/env python3
"""Install the reviewed fingerprint experiment, without starting or initializing it."""
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent
DEST=Path('/opt/void-fingerprint')
if os.getuid()!=0:
    raise SystemExit('Run with sudo after prepare.py and tests pass.')
for target in (DEST, Path('/var/lib/void-fingerprint'),
               Path('/etc/dbus-1/system.d/void-fingerprint.conf'),
               Path('/etc/sv/void-open-fprintd'), Path('/etc/sv/void-python-validity'),
               Path('/var/log/void-open-fprintd'), Path('/var/log/void-python-validity'),
               Path('/etc/elogind/system-sleep/90-void-fingerprint')):
    if any(path.is_symlink() for path in (target, *target.parents)):
        raise SystemExit(f'Refusing symlink installation path: {target}')
if DEST.exists():
    raise SystemExit(f'{DEST} exists; refusing to overwrite an existing installation.')
if subprocess.run(['xbps-query','-p','pkgver','fprintd'],capture_output=True).returncode==0:
    raise SystemExit('Stock fprintd is installed and owns the same D-Bus name. Resolve this conflict first.')
for file in ('/usr/share/dbus-1/system-services/net.reactivated.Fprint.service',
             '/etc/dbus-1/system.d/void-fingerprint.conf',
             '/etc/sv/void-open-fprintd','/etc/sv/void-python-validity',
             '/etc/elogind/system-sleep/90-void-fingerprint'):
    if Path(file).exists():raise SystemExit(f'Refusing to overwrite {file}')
for name in ('cryptography','usb','dbus','gi','yaml'):__import__(name)
if not (ROOT/'build/python-validity/validitysensor/init.py').is_file():
    raise SystemExit('Run prepare.py as your normal user first.')
subprocess.run(['/usr/bin/python3','-B','-m','unittest','discover','-s','tests'],cwd=ROOT,check=True)
DEST.mkdir(mode=0o755)
for repo in ('python-validity','open-fprintd'):
    shutil.copytree(ROOT/'build'/repo,DEST/repo,ignore=shutil.ignore_patterns('__pycache__'))
# Immutable-to-users installation; runtime state is root-only.
for path in DEST.rglob('*'):
    path.chmod(0o755 if path.is_dir() else 0o644)
state=Path('/var/lib/void-fingerprint')
state.mkdir(mode=0o700,exist_ok=True)
state.chmod(0o700)
policy=Path('/etc/dbus-1/system.d/void-fingerprint.conf')
policy.write_text('''<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN" "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
 <policy context="default">
  <allow send_destination="net.reactivated.Fprint"/>
  <deny send_interface="io.github.uunicorn.Fprint.Device"/>
 </policy>
 <policy user="root">
  <allow own="net.reactivated.Fprint"/>
  <allow send_interface="io.github.uunicorn.Fprint.Device"/>
 </policy>
</busconfig>
''')
for name,repo,entry in (('void-open-fprintd','open-fprintd','open-fprintd'),
                        ('void-python-validity','python-validity','dbus-service')):
    directory=Path('/etc/sv')/name
    directory.mkdir()
    script=directory/'run'
    script.write_text(f'''#!/bin/sh
exec 2>&1
umask 077
export PYTHONPATH=/opt/void-fingerprint/{repo}
exec /usr/bin/python3 /opt/void-fingerprint/{repo}/dbus_service/{entry}
''')
    script.chmod(0o755)
    logdir=Path('/var/log')/name
    logdir.mkdir(mode=0o700,exist_ok=True)
    (directory/'log').mkdir()
    logger=directory/'log/run'
    logger.write_text(f'#!/bin/sh\numask 077\nexec svlogd -tt {logdir}\n')
    logger.chmod(0o755)
    (directory/'down').touch() # Explicit sv up is required for each test.
# Services are deliberately not linked into /var/service here.
hook=Path('/etc/elogind/system-sleep/90-void-fingerprint')
hook.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(ROOT/'sleep-hook', hook)
hook.chmod(0o755)
subprocess.run(['busctl','--system','call','org.freedesktop.DBus','/org/freedesktop/DBus',
                'org.freedesktop.DBus','ReloadConfig'],check=True)
print('Installed under /opt/void-fingerprint. No daemon started; authentication unchanged.')
print('Reader initialization and enrollment remain separate steps. See fingerprint/README.md.')
