#!/bin/sh
set -eu
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$src/setup/setup.py" "$@"
