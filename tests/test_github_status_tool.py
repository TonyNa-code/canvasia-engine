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
            "git@github.com:TonyNa-code/tony-na-engine.git": "TonyNa-code/tony-na-engine",
            "ssh://git@ssh.github.com:443/TonyNa-code/tony-na-engine.git": "TonyNa-code/tony-na-engine",
            "ssh://git@github.com/TonyNa-code/tony-na-engine.git": "TonyNa-code/tony-na-engine",
            "https://github.com/TonyNa-code/tony-na-engine.git": "TonyNa-code/tony-na-engine",
            "https://github.com/TonyNa-code/tony-na-engine": "TonyNa-code/tony-na-engine",
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
                    "TonyNa-code/tony-na-engine",
                    "--sha",
                    "d33586a51f417505471243629f2d530ef49b5e74",
                    "--input-json",
                    str(payload_path),
                    "--json-report",
                    str(report_path),
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


if __name__ == "__main__":
    unittest.main()
