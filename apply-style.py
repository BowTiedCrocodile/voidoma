#!/usr/bin/env python3
"""Compatibility entry point: install the bundle with a backup."""
from pathlib import Path
import subprocess
import sys
subprocess.run([sys.executable, str(Path(__file__).with_name('setup.py')), '--backup', *sys.argv[1:]], check=True)
