from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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
        native_runtime_bundle = report["nativeRuntimeBundle"]
        summary = report["summary"]
        maintenance_plan = report["maintenancePlan"]

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
        self.assertEqual(module_guard["firstRequirement"]["script"], "../export_player_template/runtime_visual_comfort.js")
        self.assertEqual(module_guard["lastRequirement"]["script"], "./modules/command_palette.js")
        self.assertEqual(summary["moduleGuardStatus"], "passed")
        self.assertEqual(summary["moduleGuardRequirementCount"], module_guard["requirementCount"])
        self.assertEqual(native_runtime_bundle["status"], "passed")
        self.assertGreaterEqual(native_runtime_bundle["moduleCount"], 16)
        self.assertEqual(native_runtime_bundle["moduleCount"], native_runtime_bundle["bundledModuleCount"])
        self.assertEqual(native_runtime_bundle["missingSourceConstants"], [])
        self.assertEqual(native_runtime_bundle["staleSourceConstants"], [])
        self.assertEqual(native_runtime_bundle["missingFromBundle"], [])
        self.assertEqual(native_runtime_bundle["staleBundleFiles"], [])
        self.assertEqual(native_runtime_bundle["missingImportFiles"], [])
        self.assertEqual(native_runtime_bundle["importedNotBundled"], [])
        self.assertEqual(native_runtime_bundle["duplicateRequiredConstants"], [])
        self.assertEqual(summary["nativeRuntimeBundleStatus"], "passed")
        self.assertEqual(summary["nativeRuntimeModuleCount"], native_runtime_bundle["moduleCount"])
        self.assertEqual(summary["nativeRuntimeBundledModuleCount"], native_runtime_bundle["bundledModuleCount"])
        self.assertGreaterEqual(summary["maintenanceActionCount"], 1)
        self.assertEqual(summary["maintenanceActionCount"], len(maintenance_plan))
        self.assertEqual(summary["topMaintenancePriority"], maintenance_plan[0]["priority"])
        self.assertTrue(
            any(action["area"] == "prototype_editor/app.js" for action in maintenance_plan),
            "The largest editor file should stay visible in the preventive maintenance roadmap.",
        )
        for action in maintenance_plan:
            self.assertIn(action["priority"], {"P0", "P1", "P2", "P3"})
            self.assertTrue(action["title"])
            self.assertTrue(action["evidence"])
            self.assertTrue(action["nextStep"])

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
            self.assertIn("Native Runtime bundle: passed", completed.stdout)
            payload = json.loads(json_report.read_text(encoding="utf-8"))
            markdown = markdown_report.read_text(encoding="utf-8")
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["moduleGuard"]["status"], "passed")
            self.assertEqual(payload["moduleGuard"]["appGlobalsMissingFromGuard"], [])
            self.assertEqual(payload["nativeRuntimeBundle"]["status"], "passed")
            self.assertIn("knownTestDebtCount", payload["summary"])
            self.assertIn("maintenancePlan", payload)
            self.assertGreaterEqual(payload["summary"]["maintenanceActionCount"], 1)
            self.assertIn("# Canvasia Engine Maintainability Report", markdown)
            self.assertIn("## File Budgets", markdown)
            self.assertIn("## Maintenance Roadmap", markdown)
            self.assertIn("## Startup Guard Consistency", markdown)
            self.assertIn("## Native Runtime Bundle Parity", markdown)
            self.assertIn("App globals covered", markdown)
            self.assertIn("Maintenance roadmap:", completed.stdout)
            self.assertIn("Next maintenance actions:", completed.stdout)

    def test_native_runtime_bundle_guard_flags_imported_helper_missing_from_export_tuple(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            native_dir = root / "native_runtime"
            native_dir.mkdir()
            player_path = native_dir / "runtime_player.py"
            helper_path = native_dir / "runtime_helper.py"
            run_editor_path = root / "run_editor.py"
            player_path.write_text("from .runtime_helper import helper\n", encoding="utf-8")
            helper_path.write_text("def helper():\n    return True\n", encoding="utf-8")
            run_editor_path.write_text(
                "\n".join(
                    [
                        'NATIVE_RUNTIME_PLAYER_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "runtime_player.py"',
                        'NATIVE_RUNTIME_HELPER_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "runtime_helper.py"',
                        'NATIVE_RUNTIME_REQUIRED_MODULE_FILES = (',
                        '    (NATIVE_RUNTIME_PLAYER_SOURCE, NATIVE_RUNTIME_PLAYER_NAME),',
                        ')',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with (
                mock.patch.object(self.maintainability, "NATIVE_RUNTIME_DIR", native_dir),
                mock.patch.object(self.maintainability, "NATIVE_RUNTIME_PLAYER_PATH", player_path),
                mock.patch.object(self.maintainability, "RUN_EDITOR_PATH", run_editor_path),
            ):
                result = self.maintainability.evaluate_native_runtime_bundle()

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["missingFromBundle"], ["runtime_helper.py"])
            self.assertEqual(result["importedNotBundled"], ["runtime_helper.py"])


if __name__ == "__main__":
    unittest.main()
