from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT_DIR / ".github" / "workflows" / "ci.yml"
EDITOR_INDEX_PATH = ROOT_DIR / "prototype_editor" / "index.html"
SCRIPT_SRC_PATTERN = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)
TOP_LEVEL_KEY_PATTERN = re.compile(r"^([A-Za-z0-9_-]+):(?:\s|$)")


def _get_workflow_top_level_blocks() -> dict[str, str]:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    blocks: dict[str, list[str]] = {}
    current_key: str | None = None

    for line in workflow.splitlines():
        match = TOP_LEVEL_KEY_PATTERN.match(line)
        if match:
            current_key = match.group(1)
            if current_key in blocks:
                raise AssertionError(f"Duplicate top-level workflow key: {current_key}")
            blocks[current_key] = [line]
            continue

        if current_key is not None:
            blocks[current_key].append(line)

    return {key: "\n".join(lines) for key, lines in blocks.items()}


class CiWorkflowCoverageTests(unittest.TestCase):
    def test_ci_hardening_keys_are_top_level(self) -> None:
        blocks = _get_workflow_top_level_blocks()

        for key in ("on", "permissions", "concurrency", "jobs"):
            self.assertIn(key, blocks)

    def test_ci_uses_node_24_compatible_action_versions(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("actions/checkout@v7", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertIn("actions/setup-node@v7", workflow)
        self.assertNotIn("FORCE_JAVASCRIPT_ACTIONS_TO_NODE24", workflow)

    def test_ci_uses_least_privilege_permissions(self) -> None:
        blocks = _get_workflow_top_level_blocks()

        self.assertIn("contents: read", blocks["permissions"])
        self.assertNotIn("contents: write", blocks["permissions"])

    def test_ci_cancels_superseded_branch_runs(self) -> None:
        blocks = _get_workflow_top_level_blocks()

        self.assertIn("group: ${{ github.workflow }}-${{ github.ref }}", blocks["concurrency"])
        self.assertIn("cancel-in-progress: true", blocks["concurrency"])

    def test_ci_can_be_run_manually_before_release(self) -> None:
        blocks = _get_workflow_top_level_blocks()

        self.assertIn("workflow_dispatch:", blocks["on"])

    def test_ci_verify_job_has_timeout(self) -> None:
        blocks = _get_workflow_top_level_blocks()

        self.assertIn("verify:", blocks["jobs"])
        self.assertIn("timeout-minutes: 45", blocks["jobs"])

    def test_ci_workflow_coverage_test_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tests/test_ci_workflow_coverage.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_ci_workflow_coverage.py' -v",
            workflow,
        )

    def test_local_verify_tool_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tools/ci/local_verify.py", workflow)
        self.assertIn("tests/test_local_verify_tool.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_local_verify_tool.py' -v",
            workflow,
        )

    def test_github_status_tool_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tools/ci/github_status.py", workflow)
        self.assertIn("tests/test_github_status_tool.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_github_status_tool.py' -v",
            workflow,
        )

    def test_project_health_tool_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tools/ci/project_health.py", workflow)
        self.assertIn("tests/test_project_health_tool.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_project_health_tool.py' -v",
            workflow,
        )
        self.assertIn(
            "python tools/ci/project_health.py template_project --json-report verification_reports/project-health-template.json --markdown-report verification_reports/project-health-template.md",
            workflow,
        )

    def test_maintainability_check_tool_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tools/ci/maintainability_check.py", workflow)
        self.assertIn("tests/test_maintainability_check_tool.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_maintainability_check_tool.py' -v",
            workflow,
        )
        self.assertIn(
            "python tools/ci/maintainability_check.py --json-report verification_reports/maintainability.json --markdown-report verification_reports/maintainability.md",
            workflow,
        )

    def test_native_runtime_rollback_module_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_rollback.py", workflow)
        self.assertIn("tests/test_native_runtime_rollback.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_rollback.py' -v",
            workflow,
        )

    def test_native_runtime_save_thumbnail_module_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_save_thumbnails.py", workflow)
        self.assertIn("tests/test_native_runtime_save_thumbnails.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_save_thumbnails.py' -v",
            workflow,
        )

    def test_native_runtime_controller_input_module_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_input.py", workflow)
        self.assertIn("tests/test_native_runtime_input.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_input.py' -v",
            workflow,
        )

    def test_public_release_surface_guard_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tests/test_release_public_surface.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_release_public_surface.py' -v",
            workflow,
        )

    def test_editor_entrypoint_modules_are_syntax_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        html = EDITOR_INDEX_PATH.read_text(encoding="utf-8")
        module_scripts = [
            script.removeprefix("./")
            for script in SCRIPT_SRC_PATTERN.findall(html)
            if script.startswith("./modules/")
        ]

        self.assertTrue(module_scripts, "Editor entrypoint should load at least one frontend module.")
        for module_script in module_scripts:
            self.assertIn(
                f"node --check prototype_editor/{module_script}",
                workflow,
                f"{module_script} is loaded before app.js but is missing from the CI frontend syntax check.",
            )

    def test_frontend_module_unit_tests_are_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        frontend_test_files = sorted((ROOT_DIR / "tests").glob("test_frontend*.py"))

        self.assertTrue(frontend_test_files, "Frontend module tests should be present.")
        for test_file in frontend_test_files:
            test_name = test_file.name
            self.assertIn(
                f"python -m unittest discover -s tests -p '{test_name}' -v",
                workflow,
                f"{test_name} exists but is missing from the CI release tooling test step.",
            )


if __name__ == "__main__":
    unittest.main()
