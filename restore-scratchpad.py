#!/usr/bin/env python3
"""Move scratchpad windows to the current numbered workspace."""
import json
import re
import subprocess


def query(name):
    return json.loads(subprocess.check_output(['hyprctl', '-j', name]))


def dispatch(code):
    result = subprocess.check_output(['hyprctl', 'dispatch', code], text=True).strip()
    if result != 'ok':
        raise SystemExit(result)

workspace = query('activeworkspace')['id']
if workspace < 1:
    raise SystemExit('Select a numbered workspace first.')
clients = [c for c in query('clients') if c['workspace']['name'] == 'special:scratchpad']
for client in clients:
    address = client['address']
    if not re.fullmatch(r'0x[0-9a-fA-F]+', address):
        raise SystemExit('Unexpected window address.')
    dispatch('hl.dsp.window.move({window="address:' + address + '", workspace=' + str(workspace) + ', follow=false})')
for monitor in query('monitors'):
    if monitor['focused'] and monitor['specialWorkspace']['name'] == 'special:scratchpad':
        dispatch('hl.dsp.workspace.toggle_special("scratchpad")')
print(f'Moved {len(clients)} scratchpad windows to workspace {workspace}.')
