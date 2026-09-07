#!/usr/bin/env python3
"""Read fingerprint USB identity and flash metadata; never initialize or erase."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--metadata',action='store_true',help='send read-only ROM/flash information requests; normally needs sudo')
args=parser.parse_args()
sys.path.insert(0,str(ROOT/'build/python-validity'))
import usb.core
from validitysensor.usb import SupportedDevices
try:
    found=[d for d in usb.core.find(find_all=True) if (d.idVendor,d.idProduct) in {x.value for x in SupportedDevices}]
except usb.core.NoBackendError:
    raise SystemExit('USB backend unavailable. Run outside a restricted sandbox with libusb installed.')
if not found:
    raise SystemExit('No supported fingerprint reader found.')
for device in found:
    print(json.dumps({'usb_id':f'{device.idVendor:04x}:{device.idProduct:04x}', 'bus':device.bus,'address':device.address}))
    if args.metadata:
        # Deliberately bypass usb.open(), init.open(), send_init(), and all flash/db setup.
        from validitysensor.usb import usb as transport
        from validitysensor.flash import get_flash_info, get_fw_info
        transport.dev=device
        try:
            info=get_flash_info()
            firmware=get_fw_info(2) if info.partitions else None
            print(json.dumps({'flash_bytes':info.ic.size,'partition_count':len(info.partitions),
                              'firmware_present':firmware is not None}))
        except usb.core.USBError as exc:
            if exc.errno == 13:
                raise SystemExit('USB access denied. Run: sudo python3 probe.py --metadata')
            raise SystemExit(f'USB metadata query failed: {exc}')
        finally:
            # Release host resources only, with no USB reset or device reboot.
            import usb.util
            usb.util.dispose_resources(device)
            transport.dev=None
