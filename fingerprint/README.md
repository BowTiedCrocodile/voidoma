# Experimental fingerprint support for Void

An opt-in integration for the Synaptics **06cb:009a** reader using python-validity
and open-fprintd. This is not a general replacement for libfprint and has not had
an independent security audit. Password access remains enabled. LightDM/PAM
fingerprint login is not configured.

## Compatibility and status

Tested on Void x86_64 glibc, Python 3.14.7, cryptography 48.0.0, PyUSB 1.3.1, and
Hyprlock 0.9.6. Existing firmware/pairing, encrypted communication, calibration,
enrollment, normal-user verification, Hyprlock unlock, boot startup, and wake
recovery have been exercised on one laptop. After wake, fingerprint availability
can take **5–10 seconds** while the backend initializes. Password unlock remains
available during that wait. These results are not a guarantee for other devices.

Only an already initialized reader with existing firmware is supported by this
port. Automatic formatting and firmware upload are blocked. The repository and
release must never contain biometric templates, TLS/pairing keys, driver state,
firmware dumps, or unredacted hardware logs.

## Prepare as the normal user

From this directory:

```sh
sh install-deps.sh
sh fetch-sources.sh
python3 prepare.py
python3 -m unittest discover -s tests
python3 probe.py
sudo python3 probe.py --metadata
sudo python3 session-test.py
```

Git is required to fetch sources. Exact upstream revisions are in `pins.json`.
`prepare.py` refuses a different revision or dirty upstream checkout and applies
patches to disposable `build/` copies. Upstream checkouts retain their licenses.
Neither fetched nor generated sources are included in the release archive.

Run hardware probes only with the reader services stopped. The metadata probe
queries flash/firmware information without initialization or erasure. The session
test reads existing pairing information into memory and tests encrypted
communication; it briefly restarts the reader afterward to release session
resources. It does not calibrate, enroll, format, or upload firmware. If either
fails, investigate rather than running upstream factory-reset tools.

## Enroll and verify

Only after the probes show existing partitions, firmware, and a working encrypted
session:

```sh
sudo python3 start-test.py "$USER"
```

This installs root-owned code under `/opt/void-fingerprint`, private state under
`/var/lib/void-fingerprint`, a D-Bus policy, runit services, and an elogind sleep hook.
It reloads D-Bus configuration without restarting the bus. It refuses an existing
installation or a conflict with stock fprintd. Do not run `install.py` separately
before this guided command; it performs installation itself.

Starting the backend can calibrate the reader and create user storage. The prompt
asks you to type `enroll` for the right index finger, or `verify` for an existing
print. It refuses to overwrite that finger's enrollment, then verifies as your
normal user. No PAM or Hyprlock settings change during this test.

Service names are `void-open-fprintd` and `void-python-validity`. They initially
start once, with runit `down` files retained. The sleep hook stops the backend
before suspend and uses `sv up` after wake, allowing retries while USB returns.
The manager stays available for pending client requests. A linked reader service
may therefore start after sleep even before boot startup is explicitly enabled.

## Connect Hyprlock and enable boot startup

After successful verification, run without sudo:

```sh
python3 enable-hyprlock.py
```

This checks for enrollment, backs up Hyprlock's config, and adds fingerprint auth
alongside explicitly enabled password auth. It does not lock automatically.
Test Super+L with the enrolled finger, an unenrolled finger, and your password.
Then test suspend/resume. Once satisfied:

```sh
sudo python3 enable-boot.py
```

Reboot, log in through LightDM with your password, and test Super+L again. Future
normal-user verification can be run with `python3 client.py verify`.

## Guardrails and remaining risks

- Only root may register a backend or request manager Suspend/Resume.
- Enrollment and deletion require root; verification uses the caller's account
  ownership checks. Enrollment-name listing is restricted to the account owner or root. Raw debug-command passthrough is disabled.
- Automatic flash formatting and firmware upload are blocked even if unexpected
  reader state is encountered. Initialization requires a root-created marker.
- Driver state and logs are private; raw USB/TLS debug tracing is not enabled.
- Pending verification waits for backend registration and is invalidated on
  cancellation/release. The backend scan is stopped before suspend.
- This adapts an older community driver. Permission and lifecycle tests cover
  selected behavior, not every D-Bus race, driver fault, biometric spoof, or
  multi-user authentication scenario. Keep password access and treat this as
  experimental rather than a hardened authentication product.

## Diagnostics, updates, and rollback

```sh
sudo sh diagnose-resume.sh
```

Diagnostics are local-only: logs can include account names, application details,
and device identifiers. Review/redact before sharing. Never enable raw tracing
when collecting logs for a public issue. The relevant logs are
`/var/log/void-python-validity/current`, `/var/log/void-open-fprintd/current`, and
`/var/log/void-fingerprint-sleep.log`.

For installations from the earlier prototype, `repair-resume.py` updates the two
patched service files and sleep hook, backing up originals under `/opt`. Run
`prepare.py` first as the normal user, then `sudo python3 repair-resume.py "$USER"`.
This helper is not a general version-upgrade tool.

Disable Hyprlock fingerprint auth as the normal user:

```sh
python3 enable-hyprlock.py --disable
```

Disable boot startup with `sudo python3 enable-boot.py --disable`. To also stop
current operation, stop the reader before the manager:

```sh
sudo sv down /var/service/void-python-validity /var/service/void-open-fprintd
```

The sleep hook can restart linked services. To keep the experiment stopped across
sleep, remove its `/var/service/void-python-validity` symlink after stopping it
(leave the `/etc/sv` definition intact). Do not delete private state or reset the
reader merely to disable authentication. Re-enabling requires restoring that
service symlink. Do not uninstall dependencies while services are running.

## Sources and licenses

- [python-validity](https://github.com/uunicorn/python-validity), MIT.
- [open-fprintd](https://github.com/uunicorn/open-fprintd), GPL-2.0-or-later.
- [Hyprlock configuration](https://wiki.hypr.land/hypr-ecosystem/user/hyprlock/).
- [libfprint supported devices](https://fprint.freedesktop.org/supported-devices.html).

See [third-party notices](../THIRD_PARTY.md). Patches retain the licenses of the
upstream code they modify; the top-level MIT license does not override those.
