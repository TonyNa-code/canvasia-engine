from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from export_release_artifacts import write_export_release_artifact_index


class ExportReleaseArtifactsTests(unittest.TestCase):
    def test_write_export_release_artifact_index_creates_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            archive_path = Path(tmp_dir) / "CanvasiaDemo.zip"
            archive_path.write_bytes(b"demo")
            result = write_export_release_artifact_index(
                archive_path,
                "原生 Runtime 包",
                {
                    "archiveSha256": "abc123",
                    "archiveSizeBytes": 4,
                    "archiveSizeLabel": "4 B",
                    "archiveChecksumName": "CanvasiaDemo.zip.sha256",
                    "archiveChecksumPath": str(Path(tmp_dir) / "CanvasiaDemo.zip.sha256"),
                    "archiveChecksumJsonName": "CanvasiaDemo.zip.checksum.json",
                    "archiveChecksumJsonPath": str(Path(tmp_dir) / "CanvasiaDemo.zip.checksum.json"),
                },
                {
                    "archiveVerifierMacName": "verify.command",
                    "archiveVerifierMacPath": str(Path(tmp_dir) / "verify.command"),
                    "archiveVerifierLinuxName": "verify.sh",
                    "archiveVerifierLinuxPath": str(Path(tmp_dir) / "verify.sh"),
                    "archiveVerifierWindowsName": "verify.bat",
                    "archiveVerifierWindowsPath": str(Path(tmp_dir) / "verify.bat"),
                },
                {"releaseNotesName": "release-notes.md", "releaseNotesPath": str(Path(tmp_dir) / "release-notes.md")},
                [{"name": "native-runtime-release-control-report.md", "description": "发布总控报告。"}],
            )

            json_path = Path(result["releaseArtifactIndexJsonPath"])
            markdown_path = Path(result["releaseArtifactIndexPath"])
            self.assertTrue(json_path.is_file())
            self.assertTrue(markdown_path.is_file())
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["archive"]["name"], "CanvasiaDemo.zip")
            self.assertEqual(payload["archive"]["sha256"], "abc123")
            self.assertEqual(result["releaseArtifactUploadCount"], len(payload["uploadArtifacts"]))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("# 原生 Runtime 发布附件索引", markdown)
            self.assertIn("CanvasiaDemo.zip", markdown)
            self.assertIn("SHA-256", markdown)


if __name__ == "__main__":
    unittest.main()
