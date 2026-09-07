#!/bin/bash
set -eu
cd -- "$(dirname -- "$0")"
missing=0
for cmd in Hyprland hyprctl start-hyprland hyprland-dialog rofi waybar swaybg mako pipewire wpctl wireplumber brightnessctl busctl playerctl ghostty firefox thunar nm-connection-editor pavucontrol loginctl dbus-run-session python3 pgrep hyprlock hypridle grim slurp wl-copy wl-paste cliphist flock xdg-user-dir notify-send; do
    if ! command -v "$cmd" >/dev/null; then
        printf 'Missing command: %s\n' "$cmd"
        missing=1
    fi
done
if ((missing)); then exit 1; fi
python3 tools/check-release.py
# Parse the bundled include, never a possibly different installed touchpad.lua.
check_config=$(mktemp -d)
trap 'rm -rf -- "$check_config"' EXIT
mkdir -p "$check_config/hypr"
cp hyprland.lua touchpad.lua "$check_config/hypr/"
XDG_CONFIG_HOME="$check_config" Hyprland --verify-config -c "$check_config/hypr/hyprland.lua"
rofi -no-config -theme "$PWD/menu.rasi" -dump-theme >/dev/null
printf 'Static checks passed. Live input, audio, and display testing is still required.\n'
