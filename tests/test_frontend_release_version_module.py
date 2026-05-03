from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "release_version.js"


class FrontendReleaseVersionModuleTests(unittest.TestCase):
    def test_release_version_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.TonyNaEditorReleaseVersion;
            const result = {{
              fallback: tools.getProjectReleaseVersion({{}}),
              releaseVersion: tools.getProjectReleaseVersion({{ releaseVersion: " 2.4.0-beta " }}),
              buildVersion: tools.getProjectReleaseVersion({{ buildVersion: "2.3.0-preview" }}),
              base: tools.getReleaseVersionBase("2.4.0-rc1"),
              preview: tools.buildReleaseVersionFromPreset("preview", "2.4.0-rc1"),
              beta: tools.buildReleaseVersionFromPreset("beta", "2.4.0-rc1"),
              rc: tools.buildReleaseVersionFromPreset("rc", "2.4.0-beta"),
              stable: tools.buildReleaseVersionFromPreset("release", "2.4.0-preview"),
              custom: tools.buildReleaseVersionFromPreset("custom", "2.4.0-preview"),
            }};
            process.stdout.write(JSON.stringify(result));
            """
        )
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["fallback"], "1.0.0-preview")
        self.assertEqual(payload["releaseVersion"], "2.4.0-beta")
        self.assertEqual(payload["buildVersion"], "2.3.0-preview")
        self.assertEqual(payload["base"], "2.4.0")
        self.assertEqual(payload["preview"], "2.4.0-preview")
        self.assertEqual(payload["beta"], "2.4.0-beta")
        self.assertEqual(payload["rc"], "2.4.0-rc1")
        self.assertEqual(payload["stable"], "2.4.0")
        self.assertEqual(payload["custom"], "2.4.0-preview")


if __name__ == "__main__":
    unittest.main()
