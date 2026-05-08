from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT_DIR / ".github" / "workflows" / "ci.yml"
EDITOR_INDEX_PATH = ROOT_DIR / "prototype_editor" / "index.html"
SCRIPT_SRC_PATTERN = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)


class CiWorkflowCoverageTests(unittest.TestCase):
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
