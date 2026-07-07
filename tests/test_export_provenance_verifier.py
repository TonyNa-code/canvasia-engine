from __future__ import annotations

import stat
import tempfile
import unittest
from pathlib import Path

from export_provenance_verifier import (
    build_export_provenance_shell_verifier,
    build_export_provenance_verifier_script,
    build_export_provenance_windows_verifier,
    write_export_provenance_verifier_files,
)


class ExportProvenanceVerifierTests(unittest.TestCase):
    def test_build_export_provenance_verifier_script_embeds_profile_and_signature(self) -> None:
        script = build_export_provenance_verifier_script(
            provenance_file_name="engine.provenance.json",
            protection_profile="light-origin",
            engine_signature={"brand": "Canvasia", "marker": "TN"},
        )

        self.assertIn('PROVENANCE_FILE_NAME = "engine.provenance.json"', script)
        self.assertIn('EXPECTED_PROFILE = "light-origin"', script)
        self.assertIn('"brand": "Canvasia"', script)
        self.assertIn("def verify_bundle(bundle_dir: Path) -> dict:", script)

    def test_shell_and_windows_wrappers_call_generated_script(self) -> None:
        self.assertIn('python3 "verify.py" .', build_export_provenance_shell_verifier("verify.py"))
        self.assertIn('py -3 "verify.py" .', build_export_provenance_windows_verifier("verify.py"))

    def test_write_export_provenance_verifier_files_creates_all_platform_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = write_export_provenance_verifier_files(
                Path(tmp_dir),
                provenance_file_name="engine.provenance.json",
                protection_profile="light-origin",
                engine_signature={"brand": "Canvasia"},
                script_name="verify.py",
                mac_name="verify.command",
                linux_name="verify.sh",
                windows_name="verify.bat",
            )

            self.assertEqual(result["provenanceVerifierName"], "verify.py")
            for path in result["paths"]:
                self.assertTrue(path.is_file())
            self.assertTrue(Path(result["provenanceVerifierPath"]).stat().st_mode & stat.S_IXUSR)
            self.assertTrue(Path(result["provenanceVerifierMacPath"]).stat().st_mode & stat.S_IXUSR)
            self.assertFalse(Path(result["provenanceVerifierWindowsPath"]).stat().st_mode & stat.S_IXUSR)


if __name__ == "__main__":
    unittest.main()
