#!/usr/bin/env python3
"""Create a reproducible public archive from reviewed files only, without Git metadata."""
import gzip
import hashlib
import io
from pathlib import Path
import runpy
import tarfile

ROOT = Path(__file__).resolve().parents[1]
checker = runpy.run_path(str(ROOT / 'tools/check-release.py'))
files = checker['check']()
output = ROOT / 'dist'
output.mkdir(exist_ok=True)
archive = output / 'void-desktop-public.tar.gz'
contents = [(name, path.read_bytes()) for name, path in files]
sums = ''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n' for name, data in contents)
contents.append(('MANIFEST.sha256', sums.encode()))
with archive.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as gz:
    with tarfile.open(fileobj=gz, mode='w', format=tarfile.USTAR_FORMAT) as tar:
        for name, data in sorted(contents):
            info = tarfile.TarInfo('void-desktop/' + name)
            info.size = len(data)
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ''
            info.mtime = 0
            tar.addfile(info, io.BytesIO(data))
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix(archive.suffix + '.sha256').write_text(digest + '  ' + archive.name + '\n')
print(f'Created {archive.name} with {len(contents)} files; owner names and timestamps normalized.')
