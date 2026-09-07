#!/bin/bash
# Run AFTER testing Super+L and unlocking successfully.
set -eu
base="${XDG_CONFIG_HOME:-$HOME/.config}/hypr"
command -v hypridle >/dev/null
command -v hyprlock >/dev/null
[ -f "$base/hypridle.conf" ]
[ -f "$base/hyprlock.conf" ]
if [ ! -f /etc/pam.d/hyprlock ] && [ ! -f /usr/lib/pam.d/hyprlock ] && [ ! -f /usr/share/pam.d/hyprlock ]; then
    echo 'Missing hyprlock PAM configuration. Check your hyprlock package before enabling idle locking.' >&2
    exit 1
fi
touch "$base/idle-enabled"
# The compositor supplies the actual session environment.
python3 - "$base/desktop-start" <<'PY'
import shlex,subprocess,sys
command='bash '+shlex.quote(sys.argv[1])
# Lua long-bracket string avoids shell/Python quoting ambiguity.
if ']]' in command:
    raise SystemExit('Unsupported path containing ]]')
subprocess.run(['hyprctl','dispatch','hl.dsp.exec_cmd([['+command+']])'],check=True)
PY
printf 'Idle locking enabled: lock after 5 minutes; screen off after 10 minutes.\n'
