import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build/open-fprintd"))
import unittest
from unittest.mock import Mock
from openfprintd.device import Device


class VerifyWaitTests(unittest.TestCase):
    def device(self):
        dev = Mock()
        dev.target = None
        dev.suspended = True
        dev.callbacks = []
        dev.claim_sender = ':1.42'
        dev.claimed_by = 'testuser'
        dev.busy = False
        dev.proxy_call = lambda cb: Device.proxy_call(dev, cb)
        return dev

    def test_wake_request_waits_for_registration(self):
        dev = self.device()
        success, failure = Mock(), Mock()
        Device.VerifyStart(dev, 'any', ':1.42', Mock(), success, failure)
        success.assert_not_called()
        failure.assert_not_called()
        dev.target = Mock()
        Device.call_cbs(dev)
        dev.target.VerifyStart.assert_called_once_with('testuser', 'any', signature='ss')
        success.assert_called_once_with()
        failure.assert_not_called()

    def test_cancelled_pending_request_does_not_scan(self):
        dev = self.device()
        success, failure = Mock(), Mock()
        Device.VerifyStart(dev, 'any', ':1.42', Mock(), success, failure)
        Device.VerifyStop(dev, ':1.42', Mock())
        dev.target = Mock()
        Device.call_cbs(dev)
        dev.target.VerifyStart.assert_not_called()
        success.assert_not_called()
        failure.assert_called_once()

    def test_released_pending_request_does_not_scan(self):
        dev = self.device()
        success, failure = Mock(), Mock()
        Device.VerifyStart(dev, 'any', ':1.42', Mock(), success, failure)
        Device.do_release(dev)
        dev.target = Mock()
        Device.call_cbs(dev)
        dev.target.VerifyStart.assert_not_called()
        success.assert_not_called()
        failure.assert_called_once()
