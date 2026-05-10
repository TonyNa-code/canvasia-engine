from __future__ import annotations

import importlib.util
import json
import subprocess
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
    def test_scan_privacy_ignores_known_sanitization_fixture_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_path = Path(tmp_dir) / "creative_assistant_fixture.py"
            synthetic_sensitive_line = "api" + 'Key: "fake-live-value-for-release-test",'
            fixture_path.write_text(
                "\n".join(
                    [
                        'apiKey: "should-not-survive",',
                        'password = "should-not-survive"',
                        synthetic_sensitive_line,
                    ]
                ),
                encoding="utf-8",
            )

            with patch.object(prepare_preview_release, "tracked_files", return_value=[fixture_path]):
                result = prepare_preview_release.scan_privacy([])

        self.assertFalse(result["passed"])
        self.assertEqual(len(result["sensitiveFindings"]), 1)
        self.assertEqual(result["sensitiveFindings"][0]["type"], "api_key_assignment")
        self.assertEqual(result["sensitiveFindings"][0]["line"], 3)

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
        self.assertIn("### Download Verification", body)
        self.assertIn("verify_release_assets.command", body)
        self.assertIn("verify_release_assets.cmd", body)
        self.assertIn("preview-release-public-assets.sha256", body)
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
        self.assertNotIn("verify_release_assets.cmd", body)

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
            self.assertIn("verifyShell", outputs)
            self.assertIn("verifyMac", outputs)
            self.assertIn("verifyWindows", outputs)
            self.assertIn(f"{'a' * 64}  windows.zip", sha_path.read_text(encoding="utf-8"))
            checksum_payload = json.loads(checksum_json_path.read_text(encoding="utf-8"))
            shell_script = (Path(tmp_dir) / "verify_release_assets.sh").read_text(encoding="utf-8")
            windows_script = (Path(tmp_dir) / "verify_release_assets.cmd").read_text(encoding="utf-8")

        self.assertEqual(checksum_payload["shortCommit"], "abcdef1")
        self.assertEqual(checksum_payload["artifacts"][0]["name"], "windows.zip")
        self.assertEqual(checksum_payload["artifacts"][0]["sha256"], "a" * 64)
        self.assertIn("All release assets verified.", shell_script)
        self.assertIn("certutil -hashfile", windows_script)

    def test_write_outputs_can_copy_public_assets_into_upload_folder(self) -> None:
        readme_path = ROOT_DIR / "README.md"
        readme_sha256 = prepare_preview_release.file_sha256(readme_path)
        readme_size = readme_path.stat().st_size
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
                    "name": "README.md",
                    "path": "README.md",
                    "kind": "other",
                    "size": readme_size,
                    "sizeLabel": prepare_preview_release.human_size(readme_size),
                    "sha256": readme_sha256,
                }
            ],
            "rejectedArtifacts": [],
            "githubRelease": {"checked": False, "reason": "release check skipped"},
            "warnings": [],
            "readyForPreviewTag": True,
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            outputs = prepare_preview_release.write_outputs(report, Path(tmp_dir), copy_public_assets=True)
            upload_dir = Path(tmp_dir) / "preview-release-upload-assets"

            self.assertIn("uploadAssets", outputs)
            self.assertIn("uploadAssetsManifest", outputs)
            self.assertTrue((upload_dir / "README.md").is_file())
            self.assertTrue((upload_dir / "preview-release-public-assets.sha256").is_file())
            self.assertTrue((upload_dir / "preview-release-public-assets.checksum.json").is_file())
            self.assertTrue((upload_dir / "verify_release_assets.sh").is_file())
            self.assertTrue((upload_dir / "verify_release_assets.command").is_file())
            self.assertTrue((upload_dir / "verify_release_assets.cmd").is_file())
            upload_manifest = (upload_dir / "UPLOAD_ASSETS.md").read_text(encoding="utf-8")
            verifier = subprocess.run(
                ["sh", "verify_release_assets.sh"],
                cwd=upload_dir,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertIn("Upload the ready files listed below", upload_manifest)
        self.assertIn("README.md", upload_manifest)
        self.assertIn("verify_release_assets.cmd", upload_manifest)
        self.assertIn("Missing public artifacts: `0`", upload_manifest)
        self.assertEqual(verifier.returncode, 0, verifier.stderr)
        self.assertIn("All release assets verified.", verifier.stdout)


if __name__ == "__main__":
    unittest.main()
