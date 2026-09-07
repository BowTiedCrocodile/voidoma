#!/usr/bin/env python3
"""Apply the USB resume repair to an existing Void fingerprint installation."""
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
DEST = Path('/opt/void-fingerprint')
if os.getuid() != 0:
    raise SystemExit('Run with sudo, passing your desktop username.')
if len(sys.argv) != 2:
    raise SystemExit('Usage: sudo python3 repair-resume.py USERNAME')
user = pwd.getpwnam(sys.argv[1])
if user.pw_uid == 0:
    raise SystemExit('Pass your normal desktop username.')
files = ('python-validity/dbus_service/dbus-service', 'open-fprintd/openfprintd/device.py')
for name in files:
    if not (DEST / name).is_file() or not (ROOT / 'build' / name).is_file():
        raise SystemExit('Existing installation and prepared build required.')
subprocess.run(['/usr/bin/python3', '-B', '-m', 'unittest', 'discover', '-s', 'tests'], cwd=ROOT, check=True)
services = ['/var/service/void-open-fprintd', '/var/service/void-python-validity']
for service in services:
    if not Path(service).is_dir():
        raise SystemExit(f'Missing service: {service}')
backup = DEST / ('backup-resume-' + str(time.time_ns()))
backup.mkdir(mode=0o700)
for name in files:
    target = backup / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(DEST / name, target)
hook = Path('/etc/elogind/system-sleep/90-void-fingerprint')
shutil.copy2(hook, backup / 'sleep-hook')
print(f'Backup: {backup}', flush=True)
subprocess.run(['sv', '-w', '15', 'down', services[1]], check=True)
subprocess.run(['sv', '-w', '15', 'down', services[0]], check=True)
for name in files:
    target = DEST / name
    shutil.copyfile(ROOT / 'build' / name, target)
    target.chmod(0o644)
    os.chown(target, 0, 0)
shutil.copyfile(ROOT / 'sleep-hook', hook)
hook.chmod(0o755)
os.chown(hook, 0, 0)
for service in services:
    subprocess.run(['sv', 'up', service], check=True)
print('Waiting for reader registration...', flush=True)
import dbus
bus = dbus.SystemBus()
last_error = None
for attempt in range(60):
    try:
        manager = dbus.Interface(bus.get_object('net.reactivated.Fprint', '/net/reactivated/Fprint/Manager'),
                                 'net.reactivated.Fprint.Manager')
        device = dbus.Interface(bus.get_object('net.reactivated.Fprint', manager.GetDefaultDevice(timeout=2)),
                                'net.reactivated.Fprint.Device')
        fingers = device.ListEnrolledFingers(user.pw_name, timeout=2)
        print('Reader ready. Enrolled fingers: ' + ', '.join(fingers))
        break
    except dbus.DBusException as error:
        last_error = error
        time.sleep(1)
else:
    raise SystemExit(f'Reader did not recover: {last_error}')
print('Scan cancellation and driver restart repair installed. Test Super+L, then close/open the lid and test again.')
print('Password authentication remains enabled. Services are still in temporary test mode.')
