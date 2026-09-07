#!/usr/bin/env python3
"""Build a pinned, patched experiment without installing or accessing hardware."""
from pathlib import Path
import ast
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
PINS = {'python-validity': 'a6bbc21dce7b8b3c3cd92378a0b2579a2fb45920',
        'open-fprintd': 'b7073730bccca36e84484e3fcb4f8253ea038d07'}
BUILD = ROOT / 'build'
BUILD.mkdir(exist_ok=True)
for repo, revision in PINS.items():
    src = ROOT / 'sources' / repo
    if subprocess.check_output(['git', '-C', str(src), 'rev-parse', 'HEAD'], text=True).strip() != revision:
        raise SystemExit(f'Unexpected revision: {repo}')
    if subprocess.check_output(['git', '-C', str(src), 'status', '--porcelain'], text=True).strip():
        raise SystemExit(f'Upstream checkout has changes: {repo}')
    shutil.copytree(src, BUILD / repo, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git', '__pycache__'))

def patch(relative, old, new):
    path = BUILD / relative
    text = path.read_text()
    if text.count(old) != 1:
        raise SystemExit(f'Patch mismatch: {relative}')
    path.write_text(text.replace(old, new))

patch('python-validity/validitysensor/init_data_dir.py',
      "PYTHON_VALIDITY_DATA_DIR = '/var/run/python-validity/'",
      "PYTHON_VALIDITY_DATA_DIR = '/var/lib/void-fingerprint/'")
patch('python-validity/validitysensor/init_data_dir.py',
      'os.mkdir(PYTHON_VALIDITY_DATA_DIR)', 'os.mkdir(PYTHON_VALIDITY_DATA_DIR, 0o700)')
# Require a root-created marker before any normal initialization (which may write firmware/db).
patch('python-validity/validitysensor/init.py', 'def open_common():\n',
      'def open_common():\n    import os\n    if not os.path.isfile("/var/lib/void-fingerprint/allow-initialization"):\n        raise RuntimeError("Initialization not authorized; run the read-only probe first.")\n')
# Syslog is not guaranteed on Void. Runit captures stderr without raw USB/key tracing.
patch('python-validity/dbus_service/dbus-service',
      "handler = logging.handlers.SysLogHandler(address='/dev/log')",
      'handler = logging.StreamHandler(sys.stderr)')
patch('open-fprintd/openfprintd/manager.py',
      "        # TODO: polkit: make sure we're talking to a root process!",
      '        if connection.get_unix_user(sender) != 0:\n            raise dbus.exceptions.DBusException("Backend registration requires root", name="net.reactivated.Fprint.Error.PermissionDenied")')
for method in ('Suspend', 'Resume'):
    patch('open-fprintd/openfprintd/manager.py', f'    def {method}(self, sender, connection):\n',
          f'    def {method}(self, sender, connection):\n        if connection.get_unix_user(sender) != 0:\n            raise dbus.exceptions.DBusException("Requires root", name="net.reactivated.Fprint.Error.PermissionDenied")\n')
# Keep enrollment and deletion behind sudo while the experimental backend is in use.
for signature in ('DeleteEnrolledFingers(self, username, sender, connection)',
                  'DeleteEnrolledFingers2(self, sender, connection)',
                  'EnrollStart(self, finger_name, sender, connection)'):
    path=BUILD/'open-fprintd/openfprintd/device.py'
    if f'def {signature}:' not in path.read_text():
        # Upstream calls the finger argument finger rather than finger_name.
        if signature.startswith('EnrollStart'):
            signature='EnrollStart(self, finger, sender, connection)'
    patch('open-fprintd/openfprintd/device.py', f'    def {signature}:\n',
          f'    def {signature}:\n        if connection.get_unix_user(sender) != 0:\n            raise PermissionDenied()\n')
# This reader already has firmware. Never format it or replace firmware automatically.
patch('python-validity/validitysensor/init_flash.py',
      "        logging.info('Flash was not initialized yet. Formatting...')",
      "        raise RuntimeError('Automatic flash formatting is disabled in this Void port.')")
patch('python-validity/validitysensor/upload_fwext.py',
      "        logging.info('No firmware detected. Uploading...')",
      "        raise RuntimeError('Automatic firmware upload is disabled in this Void port.')")
# Debug passthrough would bypass enrollment/flash restrictions; disable it entirely.
patch('open-fprintd/openfprintd/device.py',
      "        return self.target.RunCmd(s, signature='s')",
      "        raise PermissionDenied()")
# Resume must rediscover a reader whose USB address changed during suspend.
patch('python-validity/dbus_service/dbus-service',
      "        logging.debug('In Resume')\n        tls.reset()",
      """        logging.debug('In Resume')
        from usb.util import dispose_resources
        if usb.dev is not None:
            try:
                dispose_resources(usb.dev)
            finally:
                usb.dev = None
        # Allow USB re-enumeration to complete before initializing the reader.
        for attempt in range(10):
            try:
                usb.open()
                break
            except Exception:
                if usb.dev is not None:
                    dispose_resources(usb.dev)
                    usb.dev = None
                if attempt == 9:
                    raise
                time.sleep(0.5)
        tls.reset()""")
# Do not release queued client calls until the device is ready.
patch('open-fprintd/openfprintd/device.py',
      """    def Resume(self):
        self.suspended = False

        if self.target is not None:
            self.target.Resume()

            self.call_cbs()""",
      """    def Resume(self):
        self.suspended = True
        if self.target is not None:
            self.target.Resume()
            self.call_cbs()""")
# Drain a scan before sleep; a no-op Suspend lets the USB disconnect kill it.
patch('python-validity/dbus_service/dbus-service',
      "        logging.debug('In Suspend')",
      """        logging.debug('In Suspend')
        sensor.cancel()
        worker = getattr(self, '_worker', None)
        if worker is not None:
            worker.join(timeout=3)
            if worker.is_alive():
                raise RuntimeError('Fingerprint scan did not stop before suspend')""")
p = BUILD / 'python-validity/dbus_service/dbus-service'
s = p.read_text()
assert s.count('thread.start()') == 2
s = s.replace('        thread.start()', '        self._worker = thread\n        thread.start()', 1)
s = s.replace('            thread.start()', '            self._worker = thread\n            thread.start()', 1)
p.write_text(s)
# A newly registered backend has already initialized its USB/TLS connection.
patch('open-fprintd/openfprintd/device.py',
      """        def process_offline():
            if not self.suspended:
                self.call_cbs()""",
      """        def process_offline():
            self.call_cbs()""")
# Hyprlock starts scanning as soon as PrepareForSleep(false) arrives. Queue
# that request while the backend initializes, and honor cancellation/release.
patch('open-fprintd/openfprintd/device.py',
      """                         sender_keyword='sender')
    def VerifyStart(self, finger_name, sender, connection):""",
      """                         sender_keyword='sender',
                         async_callbacks=('callback', 'errback'))
    def VerifyStart(self, finger_name, sender, connection, callback, errback):""")
patch('open-fprintd/openfprintd/device.py',
      """        self.busy = True
        return self.target.VerifyStart(self.claimed_by, finger_name, signature='ss')""",
      """        request = object()
        self._verify_request = request
        def start_when_ready():
            try:
                if (self._verify_request is not request or
                        self.owner_watcher is None or self.claim_sender != sender):
                    raise ClaimDevice()
                self.busy = True
                self.target.VerifyStart(self.claimed_by, finger_name, signature='ss')
                callback()
            except Exception as error:
                self.busy = False
                errback(error)
        self.proxy_call(start_when_ready)""")
patch('open-fprintd/openfprintd/device.py',
      """        self.busy = False
        self.target.Cancel(signature='')

    @dbus.service.signal""",
      """        self._verify_request = None
        self.busy = False
        if self.target is not None:
            self.target.Cancel(signature='')

    @dbus.service.signal""")
patch('open-fprintd/openfprintd/device.py',
      "    def do_release(self):\n",
      "    def do_release(self):\n        self._verify_request = None\n")
patch('open-fprintd/openfprintd/device.py',
      """        if self.busy:
            self.target.Cancel(signature='')
            self.busy = False""",
      """        if self.busy:
            if self.target is not None:
                self.target.Cancel(signature='')
            self.busy = False""")
# Listing enrollment names is account data too; apply the same ownership boundary
# as Claim instead of allowing arbitrary local users to enumerate other accounts.
patch('open-fprintd/openfprintd/device.py',
      """        def cb():
            callback(self.target.ListEnrolledFingers(username, signature='s'))""",
      """        uid = self.bus.get_unix_user(sender)
        if uid != 0 and username != pwd.getpwuid(uid).pw_name:
            raise PermissionDenied()
        def cb():
            try:
                callback(self.target.ListEnrolledFingers(username, signature='s'))
            except Exception as error:
                errback(error)""")
for path in BUILD.rglob('*.py'):
    ast.parse(path.read_text(), filename=str(path))
(ROOT/'pins.json').write_text(json.dumps(PINS,indent=2)+'\n')
print('Prepared pinned sources with initialization guard, root-only backend registration, and root-only enrollment/deletion.')
