#!/usr/bin/env python3
"""Validate the explicit public file list without executing installation scripts."""
import argparse
import ast
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def release_files():
    names = json.loads((ROOT / 'release-files.json').read_text())
    if not isinstance(names, list) or len(names) != len(set(names)):
        raise ValueError('Release manifest must be a list of unique relative files')
    files = []
    for name in names:
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe archive path')
        if any(p in {'.git', '__pycache__', 'sources', 'build', 'firmware', 'dist'} for p in path.parts):
            raise ValueError(f'Excluded directory in manifest: {name}')
        if re.search(r'(^|/)(backup|\.env)|\.(pyc|log|pem|key|pcap)(\.|$)|\.bak', name):
            raise ValueError(f'Private/generated file in manifest: {name}')
        full = ROOT / path
        if not full.is_file() or any(p.is_symlink() for p in (full, *full.parents)):
            raise ValueError(f'Missing file or symlink: {name}')
        files.append((name, full))
    return files


def png_check(data):
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Invalid PNG header')
    pos = 8
    chunks = []
    while pos < len(data):
        size = struct.unpack('>I', data[pos:pos+4])[0]
        kind = data[pos+4:pos+8]
        if kind not in {b'IHDR', b'IDAT', b'IEND', b'PLTE', b'tRNS', b'gAMA', b'cHRM', b'sRGB', b'bKGD', b'pHYs'}:
            raise ValueError('Unexpected PNG metadata chunk: ' + repr(kind))
        chunks.append(kind)
        pos += size + 12
    if pos != len(data) or not chunks or chunks[-1] != b'IEND':
        raise ValueError('Invalid PNG length or trailing metadata')


def check(private_terms=()):
    files = release_files()
    patterns = [
        ('personal home path', re.compile(r'/(?:home|Users)/[A-Za-z0-9_.-]+')),
        ('private key', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
        ('common credential', re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9]{32,})\b')),
        ('email address', re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')),
    ]
    errors = []
    for name, path in files:
        data = path.read_bytes()
        if path.suffix == '.png':
            png_check(data)
            continue
        text = data.decode('utf-8')
        for label, pattern in patterns:
            if pattern.search(text):
                errors.append(f'{name}: review {label}')
        for term in private_terms:
            if re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text, re.I):
                errors.append(f'{name}: private audit term found')
        first = text.splitlines()[0] if text else ''
        if path.suffix == '.py' or first.endswith('python3'):
            ast.parse(text, filename=name)
        elif first.startswith('#!') and ('/sh' in first or '/bash' in first):
            subprocess.run(['bash' if 'bash' in first else 'sh', '-n', str(path)], check=True)
        if path.suffix == '.json':
            json.loads(text)
    if errors:
        raise ValueError('\n'.join(errors))
    return files


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-term', action='append', default=[], help='Additional local-only term to reject; not saved')
    args = parser.parse_args()
    try:
        files = check(args.private_term)
    except (ValueError, OSError, SyntaxError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
    print(f'Checked {len(files)} public files: syntax, exclusions, PNG metadata, and common personal-data/credential patterns.')
    print('Pattern checks are a review aid, not proof that arbitrary sensitive data is absent.')
