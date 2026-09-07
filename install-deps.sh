#!/bin/sh
# Hyprland must be installed separately from a source you trust.
set -eu
case "${1:-}" in
    --dry-run) mode=-n ;;
    '') mode= ;;
    *) echo "Usage: sh install-deps.sh [--dry-run]" >&2; exit 2 ;;
esac
if ! command -v xbps-install >/dev/null; then
    echo 'This dependency installer requires Void Linux (XBPS).' >&2
    exit 1
fi
packages='bash python3 procps-ng dbus dbus-x11 elogind polkit xfce-polkit
hyprland-guiutils Waybar swaybg mako rofi ghostty firefox Thunar NetworkManager
network-manager-applet pavucontrol pipewire wireplumber playerctl brightnessctl
dejavu-fonts-ttf xdg-utils xdg-user-dirs util-linux bluez blueman wev libnotify hyprlock hypridle xdg-desktop-portal
xdg-desktop-portal-hyprland xdg-desktop-portal-gtk grim slurp wl-clipboard cliphist
libspa-bluetooth'
set --
for package in $packages; do
    if ! xbps-query -p pkgver "$package" >/dev/null 2>&1; then
        set -- "$@" "$package"
    fi
done
if [ "$#" -eq 0 ]; then
    echo 'All dependency packages are already installed.'
    exit 0
fi
if [ -n "$mode" ]; then
    set -- xbps-install "$mode" "$@"
else
    set -- xbps-install "$@"
fi
if [ "$(id -u)" -eq 0 ] || [ -n "$mode" ]; then
    exec "$@"
else
    exec sudo "$@"
fi
