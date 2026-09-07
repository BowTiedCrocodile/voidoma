#!/usr/bin/env python3
"""Test an encrypted session with existing firmware; no enrollment or flash writes."""
import json
import logging
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
if os.geteuid()!=0:
    raise SystemExit('Run with sudo; reader access and the host identity require root.')
sys.path.insert(0,str(ROOT/'build/python-validity'))
from validitysensor.flash import get_flash_info,get_fw_info,read_tls_flash
from validitysensor.tls import tls
from validitysensor.sensor import reboot,RebootException
import usb.core
import usb.util

# Never enable USB/TLS debug tracing or save keys to disk.
logging.basicConfig(level=logging.WARNING)
device=usb.core.find(idVendor=0x06cb,idProduct=0x009a)
if device is None:raise SystemExit('Reader 06cb:009a not found.')
from validitysensor.usb import usb as transport
transport.dev=device
started=False
try:
    info=get_flash_info()
    if not info.partitions or get_fw_info(2) is None:
        raise RuntimeError('Reader is not initialized; refusing firmware/flash setup.')
    print('Existing partitions and firmware confirmed.',flush=True)
    transport.send_init()
    started=True
    tls.parse_tls_flash(read_tls_flash())
    print('Existing pairing data parsed.',flush=True)
    tls.open()
    if not (tls.secure_rx and tls.secure_tx):
        raise RuntimeError('Encrypted session did not become active.')
    firmware=get_fw_info(2)
    if firmware is None:raise RuntimeError('Firmware metadata unavailable over encrypted session.')
    print(json.dumps({'encrypted_session':True,'firmware_version':f'{firmware.major}.{firmware.minor}',
                      'firmware_modules':len(firmware.modules)}),flush=True)
except Exception as exc:
    print(f'Session test failed: {type(exc).__name__}: {exc}',file=sys.stderr)
    sys.exit(1)
finally:
    if started:
        # Standard transient reader restart releases session resources. Not a factory reset.
        try:
            reboot()
        except RebootException:
            pass
        except Exception as exc:
            print(f'Reader restart cleanup: {type(exc).__name__}',file=sys.stderr)
    usb.util.dispose_resources(device)
    transport.dev=None
