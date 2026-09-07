"""Installer regressions use a temporary configuration root, never the real home."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = Path(self.temp.name) / 'config'
        self.env = dict(os.environ, XDG_CONFIG_HOME=str(self.config))

    def install(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'setup/setup.py'), *args],
                              env=self.env, capture_output=True, text=True)

    def test_fresh_install_and_overwrite_refusal(self):
        self.assertEqual(self.install().returncode, 0)
        self.assertTrue((self.config / 'hypr/touchpad.lua').is_file())
        self.assertNotEqual(self.install().returncode, 0)

    def test_dry_run_does_not_write(self):
        self.assertEqual(self.install('--dry-run').returncode, 0)
        self.assertFalse(self.config.exists())

    def test_backup_preserves_fingerprint_and_idle_opt_in(self):
        self.assertEqual(self.install().returncode, 0)
        lock = self.config / 'hypr/hyprlock.conf'
        block = '# BEGIN void-desktop fingerprint\nauth { fingerprint:enabled = true }\n# END void-desktop fingerprint\n'
        lock.write_text(lock.read_text() + block)
        (self.config / 'hypr/idle-enabled').touch()
        self.assertEqual(self.install('--backup').returncode, 0)
        self.assertIn(block, lock.read_text())
        self.assertTrue((self.config / 'hypr/idle-enabled').exists())
        backups = list(self.config.glob('void-desktop-backup-*'))
        self.assertEqual(len(backups), 1)
        self.assertIn(block, (backups[0] / 'hypr/hyprlock.conf').read_text())

    def test_symlink_destination_is_refused(self):
        self.config.mkdir()
        target = Path(self.temp.name) / 'elsewhere'
        target.mkdir()
        (self.config / 'hypr').symlink_to(target, target_is_directory=True)
        self.assertNotEqual(self.install('--backup').returncode, 0)
        self.assertEqual(list(target.iterdir()), [])

    def test_migrations_find_reorganized_source_files(self):
        self.assertEqual(self.install().returncode, 0)
        for name in ('apply-touchpad.py', 'apply-scratchpad-indicator.py', 'apply-terminal-binding.py'):
            result = subprocess.run([sys.executable, str(ROOT / 'setup/migrations' / name)],
                                    env=self.env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.config / 'hypr/touchpad.lua').read_bytes(),
                         (ROOT / 'config/touchpad.lua').read_bytes())
        self.assertEqual((self.config / 'hypr/workspace-status').read_bytes(),
                         (ROOT / 'scripts/workspace-status').read_bytes())

    def test_root_entry_point_works_from_another_directory(self):
        result = subprocess.run(['sh', str(ROOT / 'install.sh'), '--dry-run'],
                                cwd=self.temp.name, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.config.exists())
