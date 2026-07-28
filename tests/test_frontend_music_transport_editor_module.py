from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "music_transport_editor.js"
RUNTIME_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_music_transport.js"


class FrontendMusicTransportEditorModuleTests(unittest.TestCase):
    def test_beginner_presets_render_and_update_real_fields(self) -> None:
        script = textwrap.dedent(
            f"""
            import fs from "fs";
            import vm from "vm";
            import * as runtimeTools from {json.dumps(RUNTIME_MODULE_PATH.as_uri())};

            const controls = new Map([
              ["editorMusicLoop", {{ value: "true" }}],
              ["editorMusicStartTime", {{ value: "0" }}],
              ["editorMusicLoopStart", {{ value: "0", disabled: false }}],
              ["editorMusicLoopEnd", {{ value: "0", disabled: false }}],
              ["editorMusicRestartMode", {{ value: "continue" }}],
            ]);
            const summary = {{ textContent: "" }};
            const status = {{ textContent: "", className: "" }};
            const document = {{
              getElementById(id) {{ return controls.get(id) ?? null; }},
              querySelector(selector) {{
                if (selector === "[data-music-transport-summary]") return summary;
                if (selector === "[data-music-transport-status]") return status;
                return null;
              }},
            }};
            const context = {{ window: {{ CanvasiaRuntimeMusicTransport: runtimeTools }}, document }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(EDITOR_MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorMusicTransport;
            const html = tools.renderMusicTransportEditor({{ loop: true, loopStartSeconds: 6 }}, {{ runtimeTools }});
            const applied = tools.applyMusicTransportPreset("intro_loop", document, {{ runtimeTools }});
            const value = tools.readMusicTransportEditor({{}}, document, {{ runtimeTools }});
            process.stdout.write(JSON.stringify({{
              html,
              applied,
              value,
              summary: summary.textContent,
              status: status.textContent,
              loopStartDisabled: controls.get("editorMusicLoopStart").disabled,
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
        self.assertIn("精确播放", payload["html"])
        self.assertIn('data-music-transport-preset="intro_loop"', payload["html"])
        self.assertTrue(payload["applied"]["ok"])
        self.assertEqual(payload["value"]["loopStartSeconds"], 8)
        self.assertIn("循环 8 秒", payload["summary"])
        self.assertIn("有效", payload["status"])
        self.assertFalse(payload["loopStartDisabled"])


if __name__ == "__main__":
    unittest.main()
