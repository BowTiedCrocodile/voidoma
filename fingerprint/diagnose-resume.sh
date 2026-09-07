#!/bin/sh
# Read-only diagnostics; does not restart services or scan fingerprints.
if [ "$(id -u)" != 0 ]; then
    echo 'Run with sudo to read service logs.' >&2
    exit 1
fi
printf '\nFingerprint service status\n'
sv status /var/service/void-open-fprintd /var/service/void-python-validity
for name in void-python-validity void-open-fprintd; do
    printf '\nRecent %s log\n' "$name"
    tail -n 90 "/var/log/$name/current"
done
printf '\nSleep hook permissions\n'
ls -l /etc/elogind/system-sleep/90-void-fingerprint
printf '\nElogind processes\n'
ps -C elogind-daemon -o user,pid,args
printf '\nReader USB presence\n'
lsusb -d 06cb:009a
printf '\nRecent USB/sleep kernel events\n'
dmesg | rg '06cb|009a|usb 1-|PM: suspend|PM: resume' | sed '/SerialNumber:/d' | tail -n 35

printf '\nSleep hook log\n'
if [ -f /var/log/void-fingerprint-sleep.log ]; then
    tail -n 40 /var/log/void-fingerprint-sleep.log
fi
