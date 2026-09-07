#!/usr/bin/env python3
"""Compatibility entry point: install the bundle with a backup."""
from pathlib import Path
import subprocess
import sys
subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'setup.py'), '--backup', *sys.argv[1:]], check=True)
