import sys
from pathlib import Path
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build/open-fprintd'))
import dbus
from openfprintd.manager import Manager
from openfprintd.device import Device,PermissionDenied

class Permissions(unittest.TestCase):
    def test_unprivileged_backend_rejected(self):
        connection=Mock();connection.get_unix_user.return_value=1000
        manager=Mock();manager.devices={}
        with self.assertRaises(dbus.DBusException):
            Manager.RegisterDevice(manager,'/fake',':1.3',connection)
        self.assertEqual(manager.devices,{})

    def test_root_backend_accepted(self):
        connection=Mock();connection.get_unix_user.return_value=0
        manager=Mock();manager.devices={}
        with patch('openfprintd.manager.Device') as device:
            Manager.RegisterDevice(manager,'/real',':1.4',connection)
            device.return_value.set_target.assert_called_once_with('/real',':1.4')

    def test_unprivileged_lifecycle_rejected(self):
        connection=Mock();connection.get_unix_user.return_value=1000
        for method in (Manager.Suspend,Manager.Resume):
            with self.assertRaises(dbus.DBusException):method(Mock(),':1.3',connection)

    def test_enrollment_and_deletion_require_root(self):
        connection=Mock();connection.get_unix_user.return_value=1000
        for method,args in ((Device.EnrollStart,('right-index-finger',)),
                            (Device.DeleteEnrolledFingers,('testuser',)),
                            (Device.DeleteEnrolledFingers2,())):
            with self.assertRaises(PermissionDenied):method(Mock(),*args,':1.3',connection)


class FirmwareGuards(unittest.TestCase):
    def test_debug_passthrough_disabled_even_for_root(self):
        connection=Mock();connection.get_unix_user.return_value=0
        with self.assertRaises(PermissionDenied):
            Device.RunCmd(Mock(),'10',':1.1',connection)

    def test_no_format_on_empty_reader(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build/python-validity'))
        import validitysensor.init_flash as module
        info=Mock();info.partitions=[]
        with patch.object(module,'get_flash_info',return_value=info),patch.object(module.usb,'cmd') as command:
            with self.assertRaisesRegex(RuntimeError,'formatting is disabled'):
                module.init_flash()
            command.assert_not_called()

    def test_no_firmware_upload_if_missing(self):
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build/python-validity'))
        import validitysensor.upload_fwext as module
        with patch.object(module,'get_fw_info',return_value=None),patch.object(module,'write_hw_reg32') as write:
            with self.assertRaisesRegex(RuntimeError,'firmware upload is disabled'):
                module.upload_fwext()
            write.assert_not_called()

class EnrollmentPrivacy(unittest.TestCase):
    def test_other_account_enrollment_list_is_denied(self):
        device = Mock()
        device.bus.get_unix_user.return_value = 1000
        with patch('openfprintd.device.pwd.getpwuid') as account:
            account.return_value.pw_name = 'testuser'
            with self.assertRaises(PermissionDenied):
                Device.ListEnrolledFingers(device, 'anotheruser', ':1.3', Mock(), Mock(), Mock())
        device.proxy_call.assert_not_called()

    def test_own_account_can_list(self):
        device = Mock()
        device.bus.get_unix_user.return_value = 1000
        with patch('openfprintd.device.pwd.getpwuid') as account:
            account.return_value.pw_name = 'testuser'
            Device.ListEnrolledFingers(device, 'testuser', ':1.3', Mock(), Mock(), Mock())
        device.proxy_call.assert_called_once()

if __name__=='__main__':unittest.main()
