#!/bin/sh
set -eu
exec sudo xbps-install git python3-cryptography python3-usb python3-dbus python3-gobject python3-yaml innoextract
