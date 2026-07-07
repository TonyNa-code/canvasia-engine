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

    def test_report_tracks_file_budgets_and_direct_module_test_coverage(self) -> None:
        report = self.maintainability.build_report()
        file_paths = {item["path"] for item in report["fileBudgets"]}
        modules = report["modules"]
        module_guard = report["moduleGuard"]
        summary = report["summary"]

        self.assertEqual(report["status"], "passed")
        self.assertIn("prototype_editor/app.js", file_paths)
        self.assertIn("run_editor.py", file_paths)
        self.assertIn("native_runtime/runtime_player.py", file_paths)
        self.assertIn("export_player_template/player.js", file_paths)
        self.assertGreaterEqual(modules["moduleCount"], 80)
        self.assertEqual(modules["missingEntrypoint"], [])
        self.assertEqual(modules["staleEntrypoint"], [])
        self.assertEqual(modules["newMissingTests"], [])
        self.assertEqual(modules["missingTests"], [])
        self.assertEqual(modules["knownTestDebt"], [])
        self.assertEqual(summary["moduleCount"], summary["testedModuleCount"])
        self.assertEqual(summary["knownTestDebtCount"], 0)
        self.assertEqual(module_guard["status"], "passed")
        self.assertEqual(module_guard["requirementCount"], module_guard["entrypointGuardedScriptCount"])
        self.assertGreaterEqual(module_guard["requirementCount"], 80)
        self.assertEqual(module_guard["missingFromGuard"], [])
        self.assertEqual(module_guard["staleGuardScripts"], [])
        self.assertTrue(module_guard["orderMatches"])
        self.assertEqual(module_guard["orderMismatchPreview"], [])
        self.assertEqual(module_guard["duplicateGlobals"], [])
        self.assertEqual(module_guard["duplicateScripts"], [])
        self.assertEqual(module_guard["startupOrderIssues"], [])
        self.assertGreaterEqual(module_guard["appWindowGlobalCount"], 80)
        self.assertGreaterEqual(module_guard["guardedAppGlobalCount"], 80)
        self.assertEqual(module_guard["appGlobalsMissingFromGuard"], [])
        self.assertEqual(module_guard["allowedUnguardedAppGlobals"], ["CanvasiaEditorModuleGuard", "CanvasiaProjectMilestones"])
        self.assertIn("CanvasiaEditorAudioTimingEstimator", module_guard["guardGlobalsNotUsedByApp"])
        self.assertEqual(module_guard["firstRequirement"]["script"], "../export_player_template/runtime_conditions.js")
        self.assertEqual(module_guard["lastRequirement"]["script"], "./modules/command_palette.js")
        self.assertEqual(summary["moduleGuardStatus"], "passed")
        self.assertEqual(summary["moduleGuardRequirementCount"], module_guard["requirementCount"])

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
            self.assertIn("Startup guard: passed", completed.stdout)
            payload = json.loads(json_report.read_text(encoding="utf-8"))
            markdown = markdown_report.read_text(encoding="utf-8")
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["moduleGuard"]["status"], "passed")
            self.assertEqual(payload["moduleGuard"]["appGlobalsMissingFromGuard"], [])
            self.assertIn("knownTestDebtCount", payload["summary"])
            self.assertIn("# Canvasia Engine Maintainability Report", markdown)
            self.assertIn("## File Budgets", markdown)
            self.assertIn("## Startup Guard Consistency", markdown)
            self.assertIn("App globals covered", markdown)


if __name__ == "__main__":
    unittest.main()
