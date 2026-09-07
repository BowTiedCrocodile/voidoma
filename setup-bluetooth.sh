#!/bin/sh
# Run after installing bluez/blueman. Does not restart the shared D-Bus service.
set -eu
if [ "$(id -u)" -ne 0 ] || [ "$#" -ne 1 ]; then
    echo 'Usage: sudo sh setup-bluetooth.sh USERNAME' >&2
    exit 2
fi
desktop_user=$1
case "$desktop_user" in ''|-*|root) echo 'Specify a normal desktop user.' >&2; exit 2 ;; esac
id "$desktop_user" >/dev/null
if [ ! -d /etc/sv/bluetoothd ]; then
    echo 'Install bluez first.' >&2
    exit 1
fi
getent group bluetooth >/dev/null
usermod -a -G bluetooth "$desktop_user"
if [ ! -e /var/service/bluetoothd ] && [ ! -L /var/service/bluetoothd ]; then
    ln -s /etc/sv/bluetoothd /var/service/bluetoothd
fi
sv up bluetoothd
printf 'Bluetooth enabled. Reboot to refresh group membership and D-Bus policy before testing.\n'
