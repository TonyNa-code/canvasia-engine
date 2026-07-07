from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "tools" / "ci" / "local_verify.py"


def load_local_verify_module():
    spec = importlib.util.spec_from_file_location("local_verify", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LocalVerifyToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.local_verify = load_local_verify_module()

    def test_discovery_uses_editor_entrypoint_and_frontend_tests(self) -> None:
        module_scripts = self.local_verify.discover_editor_module_scripts()
        frontend_tests = self.local_verify.discover_frontend_tests()

        self.assertIn("modules/beginner_assets_guide.js", module_scripts)
        self.assertIn("modules/beginner_character_guide.js", module_scripts)
        self.assertIn("modules/character_presentation_panel.js", module_scripts)
        self.assertIn("modules/music_range_scope.js", module_scripts)
        self.assertIn("modules/story_template_application.js", module_scripts)
        self.assertIn("modules/story_template_panel.js", module_scripts)
        self.assertIn("modules/story_scene_structure_panel.js", module_scripts)
        self.assertIn("modules/script_importer_panel.js", module_scripts)
        self.assertIn("modules/dashboard_search_panel.js", module_scripts)
        self.assertIn("modules/release_control.js", module_scripts)
        self.assertIn("modules/project_doctor_panel.js", module_scripts)
        self.assertIn("modules/project_history_panel.js", module_scripts)
        self.assertIn("modules/project_milestones.js", module_scripts)
        self.assertIn("modules/project_milestones_panel.js", module_scripts)
        self.assertIn("modules/voice_match_review_panel.js", module_scripts)
        self.assertIn("modules/variables.js", module_scripts)
        self.assertIn("modules/visual_effects.js", module_scripts)
        self.assertIn("test_frontend_beginner_assets_guide_module.py", frontend_tests)
        self.assertIn("test_frontend_beginner_character_guide_module.py", frontend_tests)
        self.assertIn("test_frontend_character_presentation_panel_module.py", frontend_tests)
        self.assertIn("test_frontend_music_range_scope_module.py", frontend_tests)
        self.assertIn("test_frontend_story_template_application_module.py", frontend_tests)
        self.assertIn("test_frontend_story_template_panel_module.py", frontend_tests)
        self.assertIn("test_frontend_story_scene_structure_panel_module.py", frontend_tests)
        self.assertIn("test_frontend_script_importer_panel_module.py", frontend_tests)
        self.assertIn("test_frontend_dashboard_search_panel_module.py", frontend_tests)
        self.assertIn("test_frontend_project_milestones_module.py", frontend_tests)
        self.assertIn("test_frontend_project_doctor_panel_module.py", frontend_tests)
        self.assertIn("test_frontend_project_history_panel_module.py", frontend_tests)
        self.assertIn("test_frontend_project_milestones_panel_module.py", frontend_tests)
        self.assertIn("test_frontend_release_control_module.py", frontend_tests)
        self.assertIn("test_frontend_runtime_conditions_module.py", frontend_tests)
        self.assertIn("test_frontend_voice_match_review_panel_module.py", frontend_tests)
        self.assertIn("test_frontend_variables_module.py", frontend_tests)
        self.assertIn("test_frontend_visual_effects_module.py", frontend_tests)

    def test_profiles_build_expected_ci_like_steps(self) -> None:
        steps = self.local_verify.build_verify_steps("full", python_executable="python")
        commands = [" ".join(step.command) for step in steps]
        categories = {step.category for step in steps}

        self.assertIn("frontend-syntax", categories)
        self.assertIn("frontend-tests", categories)
        self.assertIn("backend-smoke", categories)
        self.assertIn("native-smoke", categories)
        self.assertIn("browser-smoke", categories)
        self.assertTrue(any("prototype_editor/modules/beginner_assets_guide.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/beginner_character_guide.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/character_presentation_panel.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/music_range_scope.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/story_template_application.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/story_template_panel.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/story_scene_structure_panel.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/script_importer_panel.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/dashboard_search_panel.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/release_control.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/project_doctor_panel.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/project_history_panel.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/project_milestones.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/project_milestones_panel.js" in command for command in commands))
        self.assertTrue(any("prototype_editor/modules/voice_match_review_panel.js" in command for command in commands))
        self.assertTrue(any("editor_local_security.py" in command for command in commands))
        self.assertTrue(any("editor_snapshot_cache.py" in command for command in commands))
        self.assertTrue(any("test_editor_infrastructure.py" in command for command in commands))
        self.assertTrue(any("test_frontend_beginner_assets_guide_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_beginner_character_guide_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_character_presentation_panel_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_music_range_scope_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_story_template_application_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_story_template_panel_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_story_scene_structure_panel_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_script_importer_panel_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_dashboard_search_panel_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_project_milestones_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_project_doctor_panel_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_project_history_panel_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_project_milestones_panel_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_release_control_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_runtime_conditions_module.py" in command for command in commands))
        self.assertTrue(any("test_frontend_voice_match_review_panel_module.py" in command for command in commands))
        self.assertTrue(any("export_player_template/runtime_conditions.js" in command for command in commands))
        self.assertTrue(any("test_renpy_export_contract.py" in command for command in commands))
        self.assertTrue(any("test_export_runtime_preload.py" in command for command in commands))
        self.assertTrue(any("test_release_public_surface.py" in command for command in commands))
        self.assertTrue(any("renpy_export.py" in command for command in commands))
        self.assertTrue(any("tools/ci/project_health.py template_project" in command for command in commands))
        self.assertTrue(any("test_browser_playwright_smoke.py" in command for command in commands))

    def test_dry_run_writes_json_report_without_running_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "local-verify.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--profile",
                    "quick",
                    "--dry-run",
                    "--json-report",
                    str(report_path),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["profile"], "quick")
            self.assertRegex(payload["generatedAt"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
            self.assertIn("available", payload["git"])
            self.assertEqual(payload["summary"]["status"], "planned")
            self.assertGreater(payload["summary"]["planned"], 10)
            self.assertIn("frontend-syntax", payload["summary"]["categories"])
            self.assertGreater(payload["summary"]["categories"]["frontend-tests"]["planned"], 10)
            self.assertEqual(payload["summary"]["failedCategories"], [])
            self.assertIsNone(payload["summary"]["firstFailedStep"])
            self.assertTrue(
                any("prototype_editor/modules/release_control.js" in " ".join(step["command"]) for step in payload["steps"])
            )

    def test_report_dir_writes_stable_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_dir = Path(tmp_dir) / "verify-reports"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--profile",
                    "syntax",
                    "--dry-run",
                    "--report-dir",
                    str(report_dir),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("Reports written:", completed.stdout)
            json_report = report_dir / "local-verify-syntax.json"
            markdown_report = report_dir / "local-verify-syntax.md"
            latest_json_report = report_dir / "local-verify-latest.json"
            latest_markdown_report = report_dir / "local-verify-latest.md"
            self.assertTrue(json_report.exists())
            self.assertTrue(markdown_report.exists())
            self.assertTrue(latest_json_report.exists())
            self.assertTrue(latest_markdown_report.exists())
            payload = json.loads(json_report.read_text(encoding="utf-8"))
            latest_payload = json.loads(latest_json_report.read_text(encoding="utf-8"))
            self.assertEqual(payload["profile"], "syntax")
            self.assertEqual(payload["generatedAt"], latest_payload["generatedAt"])
            self.assertEqual(payload["git"], latest_payload["git"])
            self.assertEqual(payload["summary"]["status"], "planned")
            markdown_text = markdown_report.read_text(encoding="utf-8")
            self.assertIn("# Canvasia Engine Local Verify Report", markdown_text)
            self.assertIn(f"- Generated: `{payload['generatedAt']}`", markdown_text)
            self.assertIn("## Git Snapshot", markdown_text)
            self.assertEqual(latest_payload["profile"], "syntax")
            self.assertIn(
                "# Canvasia Engine Local Verify Report",
                latest_markdown_report.read_text(encoding="utf-8"),
            )

    def test_standalone_json_and_markdown_reports_share_generation_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            json_report = Path(tmp_dir) / "local-verify.json"
            markdown_report = Path(tmp_dir) / "local-verify.md"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--profile",
                    "syntax",
                    "--dry-run",
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
            payload = json.loads(json_report.read_text(encoding="utf-8"))
            markdown = markdown_report.read_text(encoding="utf-8")
            self.assertIn(f"- Generated: `{payload['generatedAt']}`", markdown)
            if payload["git"].get("available"):
                self.assertIn(f"- Branch: `{payload['git']['branch']}`", markdown)
                self.assertIn(f"- Commit: `{payload['git']['shortSha']}`", markdown)

    def test_markdown_report_escapes_dynamic_cells_and_fences_output(self) -> None:
        results = [
            self.local_verify.StepResult(
                name="Verify | release\nphase",
                category="release|tests",
                command=["python", "script with spaces.py", "--name", "bad`module"],
                status="failed",
                duration_seconds=1.25,
                returncode=1,
                output_tail="first line\n```text\nnested fence\n```",
            )
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "local-verify.md"
            self.local_verify.write_markdown_report(
                report_path,
                "quick",
                results,
                generated_at="2026-05-09T00:00:00Z",
                git_snapshot={
                    "available": True,
                    "branch": "main|release",
                    "shortSha": "abc1234",
                    "dirty": {"staged": 1, "unstaged": 2, "untracked": 3, "total": 6},
                },
            )
            report = report_path.read_text(encoding="utf-8")

        self.assertIn("- Branch: `main|release`", report)
        self.assertIn("- Commit: `abc1234`", report)
        self.assertIn("- Local changes: `6`", report)
        self.assertIn("- Staged / unstaged / untracked: `1 / 2 / 3`", report)
        self.assertIn("| Verify \\| release phase | release\\|tests | failed | 1.25 |", report)
        self.assertIn("## Category Summary", report)
        self.assertIn("| release\\|tests | 0 | 1 | 0 | 1.25 |", report)
        self.assertIn("## Release Triage", report)
        self.assertIn("- Failed categories: `release|tests`", report)
        self.assertIn("- First failed step: `Verify | release phase`", report)
        self.assertIn("- Re-run command: `python 'script with spaces.py' --name 'bad'module'`", report)
        self.assertIn("## Step Details", report)
        self.assertIn("### Verify | release phase", report)
        self.assertIn("Command: `python 'script with spaces.py' --name 'bad'module'`", report)
        self.assertIn("````text\nfirst line\n```text\nnested fence\n```\n````", report)

    def test_terminal_output_helpers_format_productized_summary(self) -> None:
        step = self.local_verify.VerifyStep(
            name="Frontend syntax",
            category="frontend-syntax",
            command=["node", "--check", "prototype_editor/app.js"],
        )
        result = self.local_verify.StepResult(
            name=step.name,
            category=step.category,
            command=step.command,
            status="passed",
            duration_seconds=0.25,
            returncode=0,
        )
        summary = self.local_verify.summarize_results([result])
        header = self.local_verify.build_terminal_header_lines(
            "quick",
            [step],
            {
                "available": True,
                "branch": "main",
                "shortSha": "abc1234",
                "dirty": {"total": 2},
            },
        )
        lines = self.local_verify.build_terminal_summary_lines(
            summary,
            [result],
            git_snapshot={"available": True, "dirty": {"total": 2}},
            report_paths=[Path("verification_reports/local-verify-quick.md")],
        )

        self.assertEqual(self.local_verify.format_terminal_step_header(1, 1, step), "[01/01] Frontend syntax (frontend-syntax)")
        self.assertIn("[PASS] passed in 0.25s", self.local_verify.format_terminal_step_result(result))
        self.assertIn("Canvasia Engine Verify", header[0])
        self.assertIn("Profile: quick | Checks: 1", header[1])
        self.assertIn("Git: main @ abc1234 | local changes: 2", header[2])
        self.assertIn("Verification Summary", lines)
        self.assertTrue(any("1 passed / 0 failed / 0 planned / 0 skipped" in line for line in lines))
        self.assertIn("  - frontend-syntax: 1 pass, 0 fail, 0 plan, 0.25s", lines)
        self.assertIn("Next: checks passed; review local changes, then commit when ready.", lines)
        self.assertIn("  - verification_reports/local-verify-quick.md", lines)

    def test_runner_can_continue_after_failures_for_complete_reports(self) -> None:
        steps = [
            self.local_verify.VerifyStep(
                name="intentional failure",
                category="unit",
                command=[sys.executable, "-c", "import sys; sys.exit(7)"],
            ),
            self.local_verify.VerifyStep(
                name="second check",
                category="unit",
                command=[sys.executable, "-c", "print('second ran')"],
            ),
        ]

        fail_fast_results = self.local_verify.run_verify_steps(steps, fail_fast=True, emit_progress=False)
        self.assertEqual([result.status for result in fail_fast_results], ["failed"])
        self.assertEqual(fail_fast_results[0].returncode, 7)

        complete_results = self.local_verify.run_verify_steps(steps, fail_fast=False, emit_progress=False)
        self.assertEqual([result.status for result in complete_results], ["failed", "passed"])
        self.assertIn("second ran", complete_results[1].output_tail)

        summary = self.local_verify.summarize_results(complete_results)
        self.assertEqual(summary["failedCategories"], ["unit"])
        self.assertEqual(summary["firstFailedStep"]["name"], "intentional failure")
        self.assertEqual(summary["firstFailedStep"]["returncode"], 7)

    def test_timed_out_step_becomes_failed_result_instead_of_crashing(self) -> None:
        step = self.local_verify.VerifyStep(
            name="slow check",
            category="timeout",
            command=[sys.executable, "-c", "import time; print('started'); time.sleep(2)"],
            timeout_seconds=0.1,
        )

        result = self.local_verify.run_step(step)

        self.assertEqual(result.status, "failed")
        self.assertIsNone(result.returncode)
        self.assertIn("Command timed out after", result.output_tail)

    def test_missing_required_tools_are_reportable_failures(self) -> None:
        steps = [
            self.local_verify.VerifyStep(
                name="Node syntax: prototype_editor/app.js",
                category="frontend-syntax",
                command=["definitely-missing-canvasia-tool", "--check", "prototype_editor/app.js"],
            )
        ]

        missing_tools = self.local_verify.check_required_tools(steps)
        self.assertEqual(missing_tools, ["definitely-missing-canvasia-tool"])
        results = self.local_verify.build_missing_tool_results(steps, missing_tools)
        summary = self.local_verify.summarize_results(results)

        self.assertEqual(results[0].status, "failed")
        self.assertEqual(results[0].category, "environment")
        self.assertIn("Affected checks: Node syntax: prototype_editor/app.js", results[0].output_tail)
        self.assertEqual(summary["failedCategories"], ["environment"])
        self.assertEqual(summary["firstFailedStep"]["name"], "Missing required tool: definitely-missing-canvasia-tool")

    def test_strict_git_clean_gate_reports_clean_and_dirty_states(self) -> None:
        clean_result = self.local_verify.build_git_clean_result(
            {
                "available": True,
                "dirty": {"staged": 0, "unstaged": 0, "untracked": 0, "total": 0},
            }
        )
        dirty_result = self.local_verify.build_git_clean_result(
            {
                "available": True,
                "dirty": {"staged": 1, "unstaged": 2, "untracked": 3, "total": 6},
            }
        )
        unavailable_result = self.local_verify.build_git_clean_result(
            {
                "available": False,
                "error": "not a git repository",
            }
        )

        self.assertEqual(clean_result.status, "passed")
        self.assertEqual(clean_result.category, "git")
        self.assertIn("Git working tree is clean", clean_result.output_tail)
        self.assertEqual(dirty_result.status, "failed")
        self.assertEqual(dirty_result.returncode, 1)
        self.assertIn("Git working tree has 6 local change(s)", dirty_result.output_tail)
        self.assertIn("Staged / unstaged / untracked: 1 / 2 / 3", dirty_result.output_tail)
        self.assertEqual(unavailable_result.status, "failed")
        self.assertIn("Git status could not be checked", unavailable_result.output_tail)

    def test_porcelain_status_counts_git_change_types(self) -> None:
        counts = self.local_verify.parse_porcelain_status(" M README.md\nA  tools/example.py\n?? draft.txt\n")

        self.assertEqual(counts, {"staged": 1, "unstaged": 1, "untracked": 1, "total": 3})

    def test_git_snapshot_preserves_porcelain_leading_status_spaces(self) -> None:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        expected_dirty = self.local_verify.parse_porcelain_status(completed.stdout)

        snapshot = self.local_verify.get_git_snapshot()

        self.assertTrue(snapshot["available"])
        self.assertEqual(snapshot["dirty"], expected_dirty)


if __name__ == "__main__":
    unittest.main()
