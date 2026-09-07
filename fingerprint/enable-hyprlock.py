#!/usr/bin/env python3
"""Enable native fingerprint authentication alongside Hyprlock's password auth."""
import argparse
import os
from pathlib import Path
import shutil
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--disable', action='store_true')
args = parser.parse_args()
if os.getuid() == 0:
    raise SystemExit('Run as your desktop user, without sudo.')
config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'hypr/hyprlock.conf'
text = config.read_text()
begin = '# BEGIN void-desktop fingerprint\n'
end = '# END void-desktop fingerprint\n'
if begin in text:
    start = text.index(begin)
    finish = text.index(end, start) + len(end)
    text = text[:start] + text[finish:]
if not args.disable:
    import dbus
    import pwd
    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object('net.reactivated.Fprint', '/net/reactivated/Fprint/Manager'),
                             'net.reactivated.Fprint.Manager')
    device = dbus.Interface(bus.get_object('net.reactivated.Fprint', manager.GetDefaultDevice()),
                            'net.reactivated.Fprint.Device')
    if not device.ListEnrolledFingers(pwd.getpwuid(os.getuid()).pw_name):
        raise SystemExit('No enrolled fingers found; run the enrollment test first.')
    fragment = Path(__file__).with_name('hyprlock-fingerprint.conf').read_text()
    text = text.rstrip() + '\n\n' + begin + fragment + end
if text != config.read_text():
    backup = config.with_name(config.name + '.bak-' + str(time.time_ns()))
    shutil.copy2(config, backup)
    config.write_text(text)
    print(f'Backup: {backup}')
print('Fingerprint auth ' + ('disabled.' if args.disable else 'enabled for the next lock. Password auth remains enabled.'))
