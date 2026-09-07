#!/usr/bin/env python3
"""Enroll/verify through the experimental fprint D-Bus API, without PAM changes."""
import argparse
import os
import pwd
import sys
import dbus
import dbus.mainloop.glib
from gi.repository import GLib

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('action',choices=('list','enroll','verify'))
parser.add_argument('--user',default=pwd.getpwuid(os.getuid()).pw_name)
parser.add_argument('--finger',default='right-index-finger',choices=[f'{hand}-{finger}-finger' for hand in ('left','right') for finger in ('index','middle','ring','little')]+['left-thumb','right-thumb'])
args=parser.parse_args()
pwd.getpwnam(args.user)
dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus=dbus.SystemBus()
manager=dbus.Interface(bus.get_object('net.reactivated.Fprint','/net/reactivated/Fprint/Manager'), 'net.reactivated.Fprint.Manager')
path=manager.GetDefaultDevice()
device=dbus.Interface(bus.get_object('net.reactivated.Fprint',path),'net.reactivated.Fprint.Device')
if args.action=='list':
    print('Enrolled fingers:',', '.join(device.ListEnrolledFingers(args.user)) or 'none')
    raise SystemExit(0)
if args.action=='enroll' and args.finger in device.ListEnrolledFingers(args.user):
    raise SystemExit('That finger is already enrolled. Use verify; this client does not overwrite it.')
if args.action=='enroll' and os.getuid()!=0:
    raise SystemExit('This experimental backend requires sudo for enrollment.')
loop=GLib.MainLoop()
state={'done':False,'success':False}

def status(result,done):
    print(str(result),flush=True)
    if done:
        state['done']=True
        state['success']=result in ('enroll-completed','verify-match')
        loop.quit()

def timed_out():
    print('Timed out waiting for a scan.',flush=True)
    state['done']=True
    loop.quit()
    return False

prefix='Enroll' if args.action=='enroll' else 'Verify'
subscription=device.connect_to_signal(prefix+'Status',status)
claimed=False
try:
    device.Claim(args.user)
    claimed=True
    print(f'{args.action.title()} {args.finger} for {args.user}. Touch and lift your finger when prompted.',flush=True)
    GLib.timeout_add_seconds(120 if args.action=='enroll' else 40,timed_out)
    getattr(device,prefix+'Start')(args.finger)
    if not state['done']:loop.run()
except KeyboardInterrupt:
    print('Cancelled.',flush=True)
finally:
    if claimed:
        try:getattr(device,prefix+'Stop')()
        except dbus.DBusException:pass
        try:device.Release()
        except dbus.DBusException:pass
    subscription.remove()
raise SystemExit(0 if state['success'] else 1)
