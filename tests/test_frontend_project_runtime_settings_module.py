from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_runtime_settings.js"


class FrontendProjectRuntimeSettingsModuleTests(unittest.TestCase):
    def test_runtime_settings_helpers_sanitize_and_summarize_project_defaults(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectRuntimeSettings;
            const project = {{
              runtimeSettings: {{
                formalSaveSlotCount: 999,
                defaultTextSpeed: "fast",
                defaultDialogTheme: "paper",
                defaultUiThemeMode: "dark",
                defaultBgmVolume: "64",
                defaultSfxVolume: "bad",
                defaultVoiceVolume: -4,
                defaultVoiceEnabled: false,
              }},
            }};
            const settings = tools.getProjectRuntimeSettings(project);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              settings,
              explicitTextSpeed: tools.getEffectiveTextSpeed({{ textSpeed: "slow" }}, settings),
              defaultTextSpeed: tools.getEffectiveTextSpeed({{}}, settings),
              normalTextSpeed: tools.getEffectiveTextSpeed({{}}, {{ defaultTextSpeed: "normal" }}),
              cps: tools.getEffectiveTextCps({{}}, settings),
              bgmRatio: tools.getRuntimeVolumeRatio(settings, "defaultBgmVolume"),
              summary: tools.getRenpyRuntimeSummary(settings),
            }}));
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
        self.assertIn("getProjectRuntimeSettings", payload["keys"])
        self.assertEqual(
            payload["settings"],
            {
                "formalSaveSlotCount": 120,
                "defaultTextSpeed": "fast",
                "defaultDialogTheme": "paper",
                "defaultUiThemeMode": "dark",
                "defaultBgmVolume": 64,
                "defaultSfxVolume": 85,
                "defaultVoiceVolume": 0,
                "defaultVoiceEnabled": False,
                "defaultVoiceDuckingEnabled": True,
            },
        )
        self.assertEqual(payload["explicitTextSpeed"], "slow")
        self.assertEqual(payload["defaultTextSpeed"], "fast")
        self.assertEqual(payload["normalTextSpeed"], "")
        self.assertEqual(payload["cps"], 72)
        self.assertEqual(payload["bgmRatio"], 0.64)
        self.assertEqual(payload["summary"]["defaultTextCps"], 72)
        self.assertEqual(payload["summary"]["formalSaveSlotCount"], 120)


if __name__ == "__main__":
    unittest.main()
