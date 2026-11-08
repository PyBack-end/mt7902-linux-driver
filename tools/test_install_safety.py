import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = (ROOT / "Makefile").read_text()


class InstallSafetyTests(unittest.TestCase):
    def test_module_install_requires_explicit_authorization(self):
        self.assertIn('ALLOW_SYSTEM_INSTALL', MAKEFILE)
        self.assertIn('INSTALL MT7902E MODULE FILES', MAKEFILE)
        self.assertIn('/updates/dkms', MAKEFILE)

    def test_module_install_refuses_to_shadow_any_existing_module(self):
        self.assertIn('find "/lib/modules/$(KVER)"', MAKEFILE)
        self.assertIn('refusing to shadow or replace it', MAKEFILE)

    def test_firmware_install_and_removal_are_separately_guarded(self):
        self.assertIn('ALLOW_FIRMWARE_INSTALL', MAKEFILE)
        self.assertIn('ALLOW_FIRMWARE_REMOVAL', MAKEFILE)
        self.assertIn('INSTALL MT7902 FIRMWARE', MAKEFILE)
        self.assertIn('REMOVE MT7902 FIRMWARE', MAKEFILE)

    def test_install_targets_never_activate_or_unload_driver(self):
        recipes = [
            line.strip() for line in MAKEFILE.splitlines()
            if line.startswith('\t') and not line.lstrip().startswith('#')
        ]
        commands = '\n'.join(recipes)
        self.assertNotIn('rmmod', commands)
        self.assertNotIn('modprobe', commands)
        self.assertNotIn('modprobe -r', commands)

    def test_module_removal_verifies_recorded_hash(self):
        self.assertIn('sha256sum', MAKEFILE)
        self.assertIn('actual_hash', MAKEFILE)
        self.assertIn('expected_hash', MAKEFILE)
        self.assertIn('INSTALL_MARKER', MAKEFILE)

    def test_firmware_removal_verifies_manifest_hashes(self):
        self.assertIn('FIRMWARE_MANIFEST', MAKEFILE)
        self.assertIn('Firmware file changed since installation', MAKEFILE)

    def test_non_mutating_stage_target_exists(self):
        self.assertIn('stage: all', MAKEFILE)
        self.assertIn('STAGING_DIR', MAKEFILE)


if __name__ == "__main__":
    unittest.main()
