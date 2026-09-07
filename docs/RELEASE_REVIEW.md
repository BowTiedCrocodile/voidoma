# Public release review

## Scope and distribution

The public artifact is defined by `release-files.json`. Build it with
`python3 tools/build-release.py`. It contains source/configuration, wallpaper,
tests, documentation, and license notices. It does not include local Git metadata,
commit identities, fetched dependency repositories, generated drivers, bytecode,
logs, backups, personal shell experiments, biometric data, or vendor firmware.
Archive ownership and timestamps are normalized, and file/archive SHA-256 hashes
are generated. The local working directory is not itself the release artifact.

## Findings addressed

- Replaced personal account names in test fixtures with a generic test account.
- Excluded local author identity metadata; the repository had no commits to clean.
  Configure an appropriate public/no-reply Git author before making public commits.
- Added an explicit public file manifest and ignore rules for private/generated data.
- Checked wallpaper PNG chunks for hidden text, EXIF, or unexpected metadata.
- Added MIT licensing and retained separate upstream fingerprint license notices.
- Rewrote stale installation/fingerprint docs around the final supported workflow.
- Preserved the managed fingerprint Hyprlock block during desktop reinstallation.
- Added missing screenshot/XDG and utility dependencies; made runtime files private.
- Changed config verification to parse the bundled touchpad include in isolation.
- Restricted fingerprint enrollment-name listing to the account owner or root,
  and reject unexpected symlink paths during privileged fingerprint installation.
- Corrected test discovery assumptions and redacted kernel USB serial lines from
  the fingerprint diagnostic. Other diagnostic logs still require manual review.

## Validation

Passed: 70-file release manifest and personal-data/credential pattern checks;
PNG metadata inspection (wallpaper and README screenshot); eleven desktop/display/installer tests; eighteen fingerprint
permission/privacy/lifecycle tests; Python/shell syntax; and Hyprland 0.56.2/Rofi
configuration parsing. Temporary-directory installer checks cover dry-run behavior,
symlink refusal, overwrite refusal, backups, and preserved fingerprint/idle settings.
The archive was extracted into a temporary directory, all per-file hashes and
normalized owner/timestamp fields were checked, and all 29 tests passed from the
extracted source. Fingerprint preparation used locally cached pinned upstream
checkouts, not copies distributed in the archive. Two builds produced identical
archive hashes. No fresh-machine installation was performed.
Tests for root services and biometric behavior are not run against a clean machine
by this release audit. Earlier hardware tests confirm desktop startup, lock/unlock,
fingerprint enrollment/verification, boot, and suspend recovery on one laptop.
The audit does not modify the live desktop or authentication installation.

## Remaining limits

- Experimental fingerprint support has selected permission/lifecycle tests, not an
  independent security audit. Wake readiness can take 5–10 seconds. Upstream
  fingerprint dependencies and firmware compatibility remain external constraints.
- A clean-machine installation, multi-user fingerprint behavior, external-display
  presets on real hardware, Bluetooth audio, browser sharing, and all touchpad
  gestures still need broader testing. Battery firmware reporting is unresolved.
- Root setup scripts intentionally change system service/login configuration; use
  them only from a reviewed, trusted checkout. They are not a general package manager
  or an atomic system rollback mechanism. Account homes and configuration parents
  must not be controlled by a different user while root installation is running.
- Local backups, clipboard history, screenshots, service logs, and Git author
  settings can contain private data. Do not copy them into public issue attachments.
- Pattern scans and manual inspection found no personal identifiers or credentials
  in the intended public files; that is a scoped finding, not a universal guarantee.

Publication is a separate action. No remote repository, upload, or public commit
is created by the release tooling.

## Source layout

Configuration, runtime scripts, assets, setup/migration scripts, and supporting
docs are grouped in dedicated directories. The public manifest and release archive
use these paths. Runtime installation paths remain unchanged. Additional installer
tests cover migration source lookup and the root install entry point from another
working directory.
