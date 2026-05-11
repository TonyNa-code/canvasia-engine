from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "tools" / "ci" / "github_status.py"


def load_github_status_module():
    spec = importlib.util.spec_from_file_location("github_status", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GitHubStatusToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.github_status = load_github_status_module()

    def test_parse_github_repo_from_common_remote_urls(self) -> None:
        cases = {
            "git@github.com:TonyNa-code/canvasia-engine.git": "TonyNa-code/canvasia-engine",
            "ssh://git@ssh.github.com:443/TonyNa-code/canvasia-engine.git": "TonyNa-code/canvasia-engine",
            "ssh://git@github.com/TonyNa-code/canvasia-engine.git": "TonyNa-code/canvasia-engine",
            "https://github.com/TonyNa-code/canvasia-engine.git": "TonyNa-code/canvasia-engine",
            "https://github.com/TonyNa-code/canvasia-engine": "TonyNa-code/canvasia-engine",
        }

        for remote_url, expected in cases.items():
            with self.subTest(remote_url=remote_url):
                self.assertEqual(self.github_status.parse_github_repo_from_remote(remote_url), expected)

    def test_classify_check_runs(self) -> None:
        self.assertEqual(self.github_status.classify_check_runs([]), "missing")
        self.assertEqual(
            self.github_status.classify_check_runs([{"status": "completed", "conclusion": "success"}]),
            "success",
        )
        self.assertEqual(
            self.github_status.classify_check_runs([{"status": "completed", "conclusion": "failure"}]),
            "failure",
        )
        self.assertEqual(
            self.github_status.classify_check_runs([{"status": "in_progress", "conclusion": None}]),
            "in_progress",
        )

    def test_git_sync_helpers_classify_local_states(self) -> None:
        counts = self.github_status.parse_porcelain_status(" M README.md\nA  tools/example.py\n?? draft.txt\n")
        self.assertEqual(counts, {"staged": 1, "unstaged": 1, "untracked": 1, "total": 3})

        base = {"hasRemoteBranch": True, "dirty": {"total": 0}, "ahead": 0, "behind": 0}
        self.assertEqual(self.github_status.classify_git_sync(base), "synced")
        self.assertEqual(self.github_status.classify_git_sync({**base, "dirty": {"total": 1}}), "dirty")
        self.assertEqual(self.github_status.classify_git_sync({**base, "ahead": 2}), "ahead")
        self.assertEqual(self.github_status.classify_git_sync({**base, "behind": 1}), "behind")
        self.assertEqual(self.github_status.classify_git_sync({**base, "ahead": 1, "behind": 1}), "diverged")
        self.assertEqual(self.github_status.classify_git_sync({**base, "hasRemoteBranch": False}), "no_remote")
        self.assertFalse(self.github_status.refresh_remote_tracking_branch(""))

    def test_status_payload_can_include_git_snapshot(self) -> None:
        payload = self.github_status.build_status_payload(
            "TonyNa-code/canvasia-engine",
            "d33586a51f417505471243629f2d530ef49b5e74",
            [{"status": "completed", "conclusion": "success"}],
            git_snapshot={
                "syncStatus": "synced",
                "syncLabel": "已同步",
                "remoteRefreshRequested": True,
                "remoteRefreshed": True,
            },
        )

        self.assertEqual(payload["git"]["syncStatus"], "synced")
        self.assertIn("本地同步：已同步", self.github_status.format_status_text(payload))
        self.assertIn("远端刷新：已刷新", self.github_status.format_status_text(payload))

    def test_transient_github_network_errors_render_as_status(self) -> None:
        self.assertTrue(
            self.github_status.is_transient_github_error(
                RuntimeError("无法连接 GitHub API：<urlopen error _ssl.c:1015: handshake operation timed out>")
            )
        )
        payload = self.github_status.build_status_payload(
            "TonyNa-code/canvasia-engine",
            "d33586a51f417505471243629f2d530ef49b5e74",
            [],
            status_override="network_error",
            error_message="无法连接 GitHub API：handshake operation timed out",
        )

        self.assertEqual(payload["status"], "network_error")
        self.assertEqual(payload["statusLabel"], "网络暂时不可用")
        status_text = self.github_status.format_status_text(payload)
        self.assertIn("状态查询提示：无法连接 GitHub API", status_text)
        self.assertIn("这是网络/API 查询问题，不代表 CI 已失败", status_text)
        self.assertNotIn("还没有查到 GitHub Actions 检查", status_text)

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "network-status.md"
            self.github_status.write_markdown_report(report_path, payload)
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("- Query note: `无法连接 GitHub API：handshake operation timed out`", report)
            self.assertIn("GitHub API was temporarily unreachable", report)
            self.assertNotIn("| Check | Status | Conclusion | Link |", report)

    def test_network_error_messages_are_report_safe(self) -> None:
        noisy_message = "无法连接 GitHub API：\n`handshake` operation timed out\n请稍后重试"
        payload = self.github_status.build_status_payload(
            "TonyNa-code/canvasia-engine",
            "d33586a51f417505471243629f2d530ef49b5e74",
            [],
            status_override="network_error",
            error_message=noisy_message,
        )

        self.assertEqual(payload["error"], "无法连接 GitHub API： `handshake` operation timed out 请稍后重试")
        self.assertIn("状态查询提示：无法连接 GitHub API： `handshake`", self.github_status.format_status_text(payload))
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "network-status.md"
            self.github_status.write_markdown_report(report_path, payload)
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("- Query note: `无法连接 GitHub API： 'handshake' operation timed out 请稍后重试`", report)

    def test_markdown_report_escapes_dynamic_cells_and_compacts_annotations(self) -> None:
        payload = self.github_status.build_status_payload(
            "TonyNa-code/canvasia-engine",
            "d33586a51f417505471243629f2d530ef49b5e74",
            [
                {
                    "id": 7,
                    "name": "verify | smoke\nphase",
                    "status": "completed",
                    "conclusion": "failure",
                    "details_url": "https://github.com/example/actions/runs/7",
                    "output": {"annotations_count": 1, "annotations_url": "https://api.github.com/example"},
                }
            ],
            annotations_by_run={
                "7": [
                    {
                        "path": "tests/test_status.py",
                        "start_line": 12,
                        "message": "first line\nsecond line",
                    }
                ]
            },
        )

        status_text = self.github_status.format_status_text(payload)
        self.assertIn("- tests/test_status.py:12 first line second line", status_text)
        self.assertNotIn("first line\nsecond line", status_text)

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "status.md"
            self.github_status.write_markdown_report(report_path, payload)
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("| verify \\| smoke phase | completed | failure |", report)
            self.assertIn("- `tests/test_status.py:12` first line second line", report)
            self.assertNotIn("first line\nsecond line", report)

    def test_cli_can_render_saved_check_run_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            payload_path = Path(tmp_dir) / "check-runs.json"
            report_path = Path(tmp_dir) / "status.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "check_runs": [
                            {
                                "id": 1,
                                "name": "verify",
                                "status": "completed",
                                "conclusion": "success",
                                "details_url": "https://github.com/example/actions/runs/1",
                                "output": {"annotations_count": 0, "annotations_url": ""},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--repo",
                    "TonyNa-code/canvasia-engine",
                    "--sha",
                    "d33586a51f417505471243629f2d530ef49b5e74",
                    "--input-json",
                    str(payload_path),
                    "--json-report",
                    str(report_path),
                    "--skip-git",
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("GitHub CI 状态：通过", completed.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "success")
            self.assertEqual(report["runs"][0]["name"], "verify")
            self.assertEqual(report["git"], {})


if __name__ == "__main__":
    unittest.main()
