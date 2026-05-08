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

        self.assertIn("modules/release_control.js", module_scripts)
        self.assertIn("modules/variables.js", module_scripts)
        self.assertIn("modules/visual_effects.js", module_scripts)
        self.assertIn("test_frontend_release_control_module.py", frontend_tests)
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
        self.assertTrue(any("prototype_editor/modules/release_control.js" in command for command in commands))
        self.assertTrue(any("test_frontend_release_control_module.py" in command for command in commands))
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
            self.assertEqual(payload["summary"]["status"], "planned")
            self.assertGreater(payload["summary"]["planned"], 10)
            self.assertTrue(
                any("prototype_editor/modules/release_control.js" in " ".join(step["command"]) for step in payload["steps"])
            )


if __name__ == "__main__":
    unittest.main()
