from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "sfx_transport_editor.js"
RUNTIME_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_sfx_transport.js"


class FrontendSfxTransportEditorModuleTests(unittest.TestCase):
    def test_beginner_presets_and_stop_editor_update_real_fields(self) -> None:
        script = textwrap.dedent(
            f"""
            import fs from "fs";
            import vm from "vm";
            import * as runtimeTools from {json.dumps(RUNTIME_MODULE_PATH.as_uri())};

            const controls = new Map([
              ["editorSfxChannelId", {{ value: "effect" }}],
              ["editorSfxLoop", {{ value: "false" }}],
              ["editorSfxRestartMode", {{ value: "restart", disabled: false }}],
              ["editorSfxVolume", {{ value: "100" }}],
              ["editorSfxFadeInMs", {{ value: "0" }}],
              ["editorSfxReplaceFadeOutMs", {{ value: "0", disabled: false }}],
              ["editorSfxStopChannelId", {{ value: "ambience" }}],
              ["editorSfxStopFadeOutMs", {{ value: "900" }}],
            ]);
            const summary = {{ textContent: "" }};
            const status = {{ textContent: "", className: "" }};
            const document = {{
              getElementById(id) {{ return controls.get(id) ?? null; }},
              querySelector(selector) {{
                if (selector === "[data-sfx-transport-summary]") return summary;
                if (selector === "[data-sfx-transport-status]") return status;
                return null;
              }},
            }};
            const context = {{ window: {{ CanvasiaRuntimeSfxTransport: runtimeTools }}, document }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(EDITOR_MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorSfxTransport;
            const html = tools.renderSfxTransportEditor({{ loop: false }}, {{ runtimeTools }});
            const stopHtml = tools.renderSfxStopEditor({{ channelId: "ui", fadeOutMs: 300 }}, {{ runtimeTools }});
            const applied = tools.applySfxTransportPreset("ambience", document, {{ runtimeTools }});
            const value = tools.readSfxTransportEditor({{}}, document, {{ runtimeTools }});
            const stopValue = tools.readSfxStopEditor({{}}, document, {{ runtimeTools }});
            process.stdout.write(JSON.stringify({{
              html,
              stopHtml,
              applied,
              value,
              stopValue,
              summary: summary.textContent,
              status: status.textContent,
              restartDisabled: controls.get("editorSfxRestartMode").disabled,
              replaceFadeDisabled: controls.get("editorSfxReplaceFadeOutMs").disabled,
            }}));
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("音效与环境声导演", payload["html"])
        self.assertIn('data-sfx-transport-preset="ambience"', payload["html"])
        self.assertIn("停止环境声或音效", payload["stopHtml"])
        self.assertTrue(payload["applied"]["ok"])
        self.assertEqual(
            payload["value"],
            {
                "channelId": "ambience",
                "loop": True,
                "restartMode": "continue",
                "volume": 65,
                "fadeInMs": 1200,
                "replaceFadeOutMs": 800,
            },
        )
        self.assertEqual(payload["stopValue"], {"channelId": "ambience", "fadeOutMs": 900})
        self.assertIn("环境声道持续循环", payload["summary"])
        self.assertIn("有效", payload["status"])
        self.assertFalse(payload["restartDisabled"])
        self.assertFalse(payload["replaceFadeDisabled"])


if __name__ == "__main__":
    unittest.main()
