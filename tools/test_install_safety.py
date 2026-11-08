import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAKEFILE = (ROOT / "Makefile").read_text()
CONFLICT_CHECK = ROOT / "tools" / "check_module_install_conflict.sh"


class InstallSafetyTests(unittest.TestCase):
    def test_module_install_requires_explicit_authorization(self):
        self.assertIn('ALLOW_SYSTEM_INSTALL', MAKEFILE)
        self.assertIn('INSTALL MT7902E MODULE FILES', MAKEFILE)
        self.assertIn('/updates/dkms', MAKEFILE)

    def test_module_install_uses_conflict_preflight(self):
        self.assertIn('tools/check_module_install_conflict.sh', MAKEFILE)
        self.assertTrue(CONFLICT_CHECK.is_file())

    def test_conflict_preflight_accepts_empty_module_tree(self):
        with tempfile.TemporaryDirectory() as root:
            result = subprocess.run(
                ["sh", str(CONFLICT_CHECK), "7.0.0-test", "mt7902e", root],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_conflict_preflight_rejects_in_tree_mt7921e_pci_alias(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "modules.alias").write_text(
                "alias pci:v000014C3d00007902sv*sd*bc*sc*i* mt7921e\n"
            )
            result = subprocess.run(
                ["sh", str(CONFLICT_CHECK), "7.0.0-vendor", "mt7902e", root],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already has an MT7902 PCI alias", result.stderr)

    def test_conflict_preflight_refuses_mainline_supported_kernels(self):
        with tempfile.TemporaryDirectory() as root:
            result = subprocess.run(
                ["sh", str(CONFLICT_CHECK), "7.1.0-generic", "mt7902e", root],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("upstream MT7902 support", result.stderr)

    def test_conflict_preflight_rejects_existing_module_variants(self):
        for suffix in (".ko", ".ko.gz", ".ko.xz", ".ko.zst"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as root:
                module = Path(root) / "kernel" / "drivers" / "mt7902e" / ("mt7902e" + suffix)
                module.parent.mkdir(parents=True)
                module.write_bytes(b"existing module")
                result = subprocess.run(
                    ["sh", str(CONFLICT_CHECK), "7.0.0-test", "mt7902e", root],
                    capture_output=True, text=True, check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("refusing to shadow or replace it", result.stderr)

    def test_conflict_preflight_rejects_symlinked_module(self):
        with tempfile.TemporaryDirectory() as root:
            module = Path(root) / "updates" / "dkms" / "mt7902e.ko"
            module.parent.mkdir(parents=True)
            target = Path(root) / "outside-module"
            target.write_bytes(b"existing module")
            module.symlink_to(target)
            result = subprocess.run(
                ["sh", str(CONFLICT_CHECK), "7.0.0-test", "mt7902e", root],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)

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
