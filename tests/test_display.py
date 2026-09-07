"""Run with python3 -m unittest discover -s tests from the bundle directory."""
import copy
from pathlib import Path
import runpy
import subprocess
import unittest
from unittest.mock import patch

module = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/display-menu'), run_name='display_test')
preset = module['preset']
snapshot = module['snapshot']
BASE = {'id': 0, 'name': 'eDP-1', 'width': 1920, 'height': 1080,
        'refreshRate': 60, 'x': 0, 'y': 0, 'scale': 1, 'disabled': False, 'mirrorOf': 'none'}

class Displays(unittest.TestCase):
    def setUp(self):
        self.items = [copy.deepcopy(BASE), dict(BASE, id=1, name='HDMI-A-1', x=1920)]

    def test_no_external_does_not_disable_laptop(self):
        with self.assertRaises(ValueError):
            preset([BASE], 'External only', 'HDMI-A-1')

    def test_external_enabled_before_laptop_disabled(self):
        specs = preset(self.items, 'External only', 'HDMI-A-1')
        self.assertEqual(specs[0]['output'], 'HDMI-A-1')
        self.assertFalse(specs[0]['disabled'])
        self.assertTrue(specs[1]['disabled'])

    def test_mirror_targets_internal(self):
        self.assertEqual(preset(self.items, 'Mirror', 'HDMI-A-1')[1]['mirror'], 'eDP-1')

    def test_snapshot_preserves_scale_position_and_disabled(self):
        self.items[0].update(scale=1.5, x=-1280)
        self.items[1]['disabled'] = True
        specs = snapshot(self.items)
        self.assertEqual(specs[0]['scale'], 1.5)
        self.assertEqual(specs[0]['position'], '-1280x0')
        self.assertTrue(specs[1]['disabled'])

    def test_timeout_reverts(self):
        scope = module['main'].__globals__
        import tempfile
        with tempfile.TemporaryDirectory() as runtime, patch.dict('os.environ', XDG_RUNTIME_DIR=runtime), \
             patch('sys.argv', ['display-menu']), \
             patch.dict(scope, monitors=lambda: self.items):
            from unittest.mock import Mock
            apply = Mock()
            choose = Mock(side_effect=['Extend', subprocess.TimeoutExpired('rofi', 15)])
            with patch.dict(scope, apply=apply, choose=choose):
                module['main']()
            self.assertEqual(apply.call_count, 2)
            self.assertEqual(apply.call_args.args[0], snapshot(self.items))

if __name__ == '__main__':
    unittest.main()
