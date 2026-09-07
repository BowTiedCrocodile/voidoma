#!/usr/bin/env python3
"""Start the guarded reader experiment and guide enrollment/verification."""
import argparse
import os
from pathlib import Path
import pwd
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('user')
args=parser.parse_args()
account=pwd.getpwnam(args.user)
if account.pw_uid==0 or os.geteuid()!=0:
    parser.error('Run with sudo and specify your normal desktop username.')
if not Path('/opt/void-fingerprint').exists():
    subprocess.run([sys.executable,'-B',str(ROOT/'install.py')],check=True)
else:
    raise SystemExit('An experiment is already installed. Inspect its status/logs before retrying; this script will not overwrite it.')
state=Path('/var/lib/void-fingerprint')
# This enables calibration and storage setup; patched code forbids format/fw upload.
(state/'allow-initialization').touch(mode=0o600)
services=['void-open-fprintd','void-python-validity']
started=[]
try:
    for name in services:
        link=Path('/var/service')/name
        if not link.exists():link.symlink_to(Path('/etc/sv')/name)
        for _ in range(50):
            if (link/'supervise/ok').exists():break
            time.sleep(.1)
        subprocess.run(['sv','once',str(link)],check=True)
        started.append(str(link))
        if name=='void-open-fprintd':
            for _ in range(50):
                result=subprocess.run(['busctl','--system','call','org.freedesktop.DBus','/org/freedesktop/DBus','org.freedesktop.DBus','NameHasOwner','s','net.reactivated.Fprint'],capture_output=True,text=True)
                if result.stdout.strip()=='b true':break
                time.sleep(.1)
            else:raise RuntimeError('open-fprintd did not acquire its D-Bus name')
    print('Waiting for reader calibration and registration (up to 60 seconds)...',flush=True)
    import dbus
    bus=dbus.SystemBus()
    manager=dbus.Interface(bus.get_object('net.reactivated.Fprint','/net/reactivated/Fprint/Manager'),'net.reactivated.Fprint.Manager')
    for _ in range(60):
        try:
            path=manager.GetDefaultDevice(timeout=3)
            break
        except dbus.DBusException:
            time.sleep(1)
    else:raise RuntimeError('Reader did not register; inspect /var/log/void-python-validity/current')
except BaseException:
    for service in reversed(started):subprocess.run(['sv','down',service])
    raise
client=[sys.executable,str(ROOT/'client.py')]
subprocess.run(client+['list','--user',args.user],check=True)
print('\nReader ready. Enrollment stores a fingerprint on the reader; password login is unchanged.',flush=True)
answer=input('Type enroll to enroll your right index finger, or verify if it is already enrolled: ').strip()
if answer=='enroll':
    subprocess.run(client+['enroll','--user',args.user],check=True)
elif answer!='verify':
    print('Skipped enrollment. Services remain available for testing until reboot.')
    raise SystemExit(0)
print('\nNow test verification as your normal user.',flush=True)
subprocess.run(['runuser','-u',args.user,'--',sys.executable,str(ROOT/'client.py'),'verify','--user',args.user],check=True)
print('Enrollment/verification succeeded. Authentication configuration has not been changed.')
