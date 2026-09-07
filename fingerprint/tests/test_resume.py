import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build/open-fprintd"))
"""Exercise USB replacement and delayed/failed resume without hardware."""
import ast
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]


def resume_method(method="Resume"):
    tree = ast.parse((ROOT / 'build/python-validity/dbus_service/dbus-service').read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Device')
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == method)
    fn.decorator_list = []
    namespace = dict(logging=Mock(), usb=Mock(), tls=Mock(), init=Mock(), time=Mock(), sensor=Mock())
    exec(compile(ast.Module(body=[fn], type_ignores=[]), '<resume>', 'exec'), namespace)
    return namespace


class ResumeTests(unittest.TestCase):
    def test_discards_old_handle_before_initialization(self):
        ns = resume_method()
        old = ns['usb'].dev
        def opened():
            self.assertIsNone(ns['usb'].dev)
            ns['usb'].dev = 'new reader'
        ns['usb'].open.side_effect = opened
        def initialized():
            self.assertEqual(ns['usb'].dev, 'new reader')
        ns['init'].open_common.side_effect = initialized
        with patch('usb.util.dispose_resources') as dispose:
            ns['Resume'](Mock())
            dispose.assert_called_once_with(old)
        ns['init'].open_common.assert_called_once()

    def test_waits_for_usb_to_reappear(self):
        ns = resume_method()
        ns['usb'].open.side_effect = [RuntimeError('absent'), None]
        with patch('usb.util.dispose_resources'):
            ns['Resume'](Mock())
        self.assertEqual(ns['usb'].open.call_count, 2)
        ns['time'].sleep.assert_called_once_with(0.5)
        ns['init'].open_common.assert_called_once()

    def test_missing_reader_never_initializes(self):
        ns = resume_method()
        ns['usb'].open.side_effect = RuntimeError('absent')
        with patch('usb.util.dispose_resources'), self.assertRaises(RuntimeError):
            ns['Resume'](Mock())
        self.assertEqual(ns['usb'].open.call_count, 10)
        ns['init'].open_common.assert_not_called()

    def test_failed_resume_keeps_clients_waiting(self):
        from openfprintd.device import Device
        dev = Mock()
        dev.target.Resume.side_effect = RuntimeError('absent')
        with self.assertRaises(RuntimeError):
            Device.Resume(dev)
        self.assertTrue(dev.suspended)
        dev.call_cbs.assert_not_called()


class SuspendTests(unittest.TestCase):
    def test_active_scan_is_cancelled_and_joined(self):
        ns = resume_method('Suspend')
        device = Mock()
        device._worker.is_alive.return_value = False
        ns['Suspend'](device)
        ns['sensor'].cancel.assert_called_once()
        device._worker.join.assert_called_once_with(timeout=3)

    def test_stuck_scan_reports_failure(self):
        ns = resume_method('Suspend')
        device = Mock()
        device._worker.is_alive.return_value = True
        with self.assertRaises(RuntimeError):
            ns['Suspend'](device)
