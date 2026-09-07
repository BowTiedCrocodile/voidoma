#!/usr/bin/env python3
"""Enable or disable boot startup for the installed fingerprint services."""
import argparse
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--disable', action='store_true')
args = parser.parse_args()
if os.getuid() != 0:
    raise SystemExit('Run with sudo.')
services = [Path('/etc/sv') / name for name in ('void-open-fprintd', 'void-python-validity')]
# Validate everything before changing boot policy.
for service in services:
    link = Path('/var/service') / service.name
    if not (service / 'run').is_file() or not link.is_symlink() or link.resolve() != service.resolve():
        raise SystemExit(f'Expected installed and linked service: {service.name}')
if not Path('/var/lib/void-fingerprint/allow-initialization').is_file():
    raise SystemExit('Complete the enrollment and verification setup first.')
if args.disable:
    for service in services:
        (service / 'down').touch(mode=0o644)
    print('Boot startup disabled. Current services remain running; sleep hooks may restart the reader this boot.')
else:
    for service in services:
        (service / 'down').unlink(missing_ok=True)
        subprocess.run(['sv', 'up', str(Path('/var/service') / service.name)], check=True)
    print('Fingerprint services enabled at boot. Enrollment and password settings unchanged.')
    print('After reboot: log in with your password, then test Super+L and fingerprint unlock.')
