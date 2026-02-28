import tempfile
import unittest
from pathlib import Path

from core.license_manager import LicenseManager


class LicenseManagerTests(unittest.TestCase):
    def _build_manager(self, tmp_dir: str) -> LicenseManager:
        manager = LicenseManager()
        manager.license_file = str(Path(tmp_dir) / "license.json")
        return manager

    def test_activate_and_check_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self._build_manager(tmp)
            device_hash = manager.get_device_hash()
            token = LicenseManager.create_activation_token(
                license_id="LIC_TEST_001",
                order_ref="ORDER_001",
                device_hash=device_hash,
            )

            ok, _msg = manager.activate_with_token(token)
            self.assertTrue(ok)

            valid, _message = manager.check_local_license()
            self.assertTrue(valid)

    def test_reject_device_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self._build_manager(tmp)
            token = LicenseManager.create_activation_token(
                license_id="LIC_TEST_002",
                order_ref="ORDER_002",
                device_hash="sha256:some-other-device",
            )
            ok, msg = manager.activate_with_token(token)
            self.assertFalse(ok)
            self.assertIn("device mismatch", msg.lower())

    def test_reject_tampered_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = self._build_manager(tmp)
            device_hash = manager.get_device_hash()
            token = LicenseManager.create_activation_token(
                license_id="LIC_TEST_003",
                order_ref="ORDER_003",
                device_hash=device_hash,
            )
            tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
            ok, _msg = manager.activate_with_token(tampered)
            self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
