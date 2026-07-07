from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "tools" / "ci" / "maintainability_check.py"


def load_maintainability_module():
    spec = importlib.util.spec_from_file_location("maintainability_check", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MaintainabilityCheckToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.maintainability = load_maintainability_module()

    def test_report_tracks_file_budgets_and_module_test_debt(self) -> None:
        report = self.maintainability.build_report()
        file_paths = {item["path"] for item in report["fileBudgets"]}
        modules = report["modules"]

        self.assertEqual(report["status"], "passed")
        self.assertIn("prototype_editor/app.js", file_paths)
        self.assertIn("run_editor.py", file_paths)
        self.assertIn("native_runtime/runtime_player.py", file_paths)
        self.assertIn("export_player_template/player.js", file_paths)
        self.assertGreaterEqual(modules["moduleCount"], 80)
        self.assertEqual(modules["missingEntrypoint"], [])
        self.assertEqual(modules["staleEntrypoint"], [])
        self.assertEqual(modules["newMissingTests"], [])
        self.assertIn("typewriter", modules["knownTestDebt"])
        self.assertIn("project_polish_receipt_panel", modules["knownTestDebt"])

    def test_cli_writes_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_report = Path(tmp_dir) / "maintainability.json"
            markdown_report = Path(tmp_dir) / "maintainability.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--json-report",
                    str(json_report),
                    "--markdown-report",
                    str(markdown_report),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("Canvasia maintainability: passed", completed.stdout)
            payload = json.loads(json_report.read_text(encoding="utf-8"))
            markdown = markdown_report.read_text(encoding="utf-8")
            self.assertEqual(payload["status"], "passed")
            self.assertIn("knownTestDebtCount", payload["summary"])
            self.assertIn("# Canvasia Engine Maintainability Report", markdown)
            self.assertIn("## File Budgets", markdown)


if __name__ == "__main__":
    unittest.main()
