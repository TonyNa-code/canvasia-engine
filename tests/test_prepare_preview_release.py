from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "tools" / "release" / "prepare_preview_release.py"

spec = importlib.util.spec_from_file_location("prepare_preview_release", MODULE_PATH)
prepare_preview_release = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(prepare_preview_release)


class PreviewReleaseBodyTests(unittest.TestCase):
    def test_release_body_includes_public_download_guide(self) -> None:
        report = {
            "githubActions": {"checked": True, "status": "completed", "conclusion": "success"},
            "privacy": {"sensitiveFindings": []},
            "git": {"workingTreeClean": True},
            "artifacts": [
                {
                    "name": "TonyNaEngine-macos-preview.zip",
                    "kind": "editor-package",
                    "sizeLabel": "42.0 MB",
                    "sha256": "a" * 64,
                },
                {
                    "name": "SampleGame-native_runtime-preview.zip",
                    "kind": "native-runtime",
                    "sizeLabel": "18.0 MB",
                    "sha256": "b" * 64,
                },
                {
                    "name": "SampleGame-old-native_runtime-preview.zip",
                    "kind": "native-runtime",
                    "sizeLabel": "12.0 MB",
                    "sha256": "c" * 64,
                },
            ],
        }

        body = prepare_preview_release.render_release_body(report)

        self.assertIn("## Download Guide", body)
        self.assertIn("### Recommended Assets", body)
        self.assertIn("TonyNaEngine-macos-preview.zip", body)
        self.assertIn("SampleGame-native_runtime-preview.zip", body)
        self.assertNotIn("SampleGame-old-native_runtime-preview.zip", body)
        self.assertIn("Try the editor without cloning source", body)
        self.assertIn("Native Runtime packages include their own validation reports", body)
        self.assertIn("additional local artifact", body)
        self.assertIn("## Verification", body)
        self.assertIn("Privacy scan findings: `0`", body)

    def test_release_body_has_source_fallback_when_no_artifacts(self) -> None:
        report = {
            "githubActions": {"checked": False, "reason": "network skipped"},
            "privacy": {"sensitiveFindings": []},
            "git": {"workingTreeClean": True},
            "artifacts": [],
        }

        body = prepare_preview_release.render_release_body(report)

        self.assertIn("No binary package is attached", body)
        self.assertIn("Source code archive", body)
        self.assertIn("GitHub Actions: not checked", body)

    def test_release_comparison_uses_public_artifacts_only(self) -> None:
        artifacts = [
            {
                "name": "Game-new-native_runtime-preview.zip",
                "kind": "native-runtime",
                "sizeLabel": "10.0 MB",
                "sha256": "a" * 64,
                "releaseCheckSummary": {"errors": 0},
            },
            {
                "name": "Game-old-native_runtime-preview.zip",
                "kind": "native-runtime",
                "sizeLabel": "8.0 MB",
                "sha256": "b" * 64,
                "releaseCheckSummary": {"errors": 0},
            },
            {
                "name": "macos.tar.gz",
                "kind": "editor-suite",
                "sizeLabel": "80.0 MB",
                "sha256": "c" * 64,
                "releaseCheckSummary": {"errors": 0},
            },
        ]
        captured_artifacts = []

        def fake_github_release_status(_git, release_artifacts, **_kwargs):
            captured_artifacts.extend(release_artifacts)
            return {"checked": False, "reason": "release check skipped"}

        with patch.object(prepare_preview_release, "git_info", return_value={"workingTreeClean": True}):
            with patch.object(prepare_preview_release, "discover_artifacts", return_value=artifacts):
                with patch.object(prepare_preview_release, "github_ci_status", return_value={"checked": False, "reason": "network skipped"}):
                    with patch.object(prepare_preview_release, "scan_privacy", return_value={"sensitiveFindings": [], "largeTrackedFiles": [], "passed": True}):
                        with patch.object(prepare_preview_release, "github_release_status", side_effect=fake_github_release_status):
                            report = prepare_preview_release.build_report(
                                SimpleNamespace(
                                    extra_sensitive=[],
                                    max_artifacts=12,
                                    skip_network=False,
                                    skip_release_check=True,
                                    release_tag="",
                                )
                            )

        self.assertEqual([artifact["name"] for artifact in report["publicArtifacts"]], ["macos.tar.gz", "Game-new-native_runtime-preview.zip"])
        self.assertEqual([artifact["name"] for artifact in captured_artifacts], ["macos.tar.gz", "Game-new-native_runtime-preview.zip"])
        self.assertEqual(len(report["artifacts"]), 3)

    def test_write_outputs_includes_public_checksum_files(self) -> None:
        report = {
            "generatedAt": "2026-05-04T00:00:00+08:00",
            "git": {
                "branch": "main",
                "commit": "abcdef1234567890",
                "shortCommit": "abcdef1",
                "workingTreeClean": True,
            },
            "githubActions": {"checked": False, "reason": "network skipped"},
            "privacy": {"passed": True, "sensitiveFindings": [], "largeTrackedFiles": []},
            "artifacts": [],
            "publicArtifacts": [
                {
                    "name": "windows.zip",
                    "path": "exports/windows.zip",
                    "kind": "editor-suite",
                    "size": 123,
                    "sizeLabel": "123 B",
                    "sha256": "a" * 64,
                }
            ],
            "rejectedArtifacts": [],
            "githubRelease": {"checked": False, "reason": "release check skipped"},
            "warnings": [],
            "readyForPreviewTag": True,
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            outputs = prepare_preview_release.write_outputs(report, Path(tmp_dir))
            sha_path = Path(tmp_dir) / "preview-release-public-assets.sha256"
            checksum_json_path = Path(tmp_dir) / "preview-release-public-assets.checksum.json"

            self.assertIn("sha256", outputs)
            self.assertIn("checksumJson", outputs)
            self.assertIn(f"{'a' * 64}  windows.zip", sha_path.read_text(encoding="utf-8"))
            checksum_payload = json.loads(checksum_json_path.read_text(encoding="utf-8"))

        self.assertEqual(checksum_payload["shortCommit"], "abcdef1")
        self.assertEqual(checksum_payload["artifacts"][0]["name"], "windows.zip")
        self.assertEqual(checksum_payload["artifacts"][0]["sha256"], "a" * 64)


if __name__ == "__main__":
    unittest.main()
