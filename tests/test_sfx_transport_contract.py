from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_sfx_transport import (
    apply_sfx_block_to_channel_state,
    sanitize_sfx_stop,
    sanitize_sfx_transport,
)
from renpy_export import render_story_block


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_sfx_transport.js"
RENPY_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "renpy_exporter.js"


class SfxTransportContractTests(unittest.TestCase):
    def test_web_and_native_normalization_and_state_reduction_stay_aligned(self) -> None:
        scenarios = [
            {},
            {"channelId": "ambience", "loop": True, "volume": 62, "fadeInMs": 350},
            {"channelId": "ui", "loop": False, "restartMode": "continue", "volume": -2},
            {"channelId": "broken", "replaceFadeOutMs": 999999, "restartMode": "broken"},
        ]
        stops = [{}, {"channelId": "ambience", "fadeOutMs": 900}, {"channelId": "broken", "fadeOutMs": -1}]
        blocks = [
            {
                "id": "rain-a",
                "type": "sfx_play",
                "assetId": "rain",
                "channelId": "ambience",
                "loop": True,
                "restartMode": "continue",
                "volume": 65,
            },
            {"type": "sfx_play", "assetId": "click", "channelId": "effect", "loop": False},
            {"type": "sfx_stop", "channelId": "ambience", "fadeOutMs": 700},
        ]
        script = textwrap.dedent(
            f"""
            import {{
              applySfxBlockToChannelState,
              sanitizeSfxStop,
              sanitizeSfxTransport,
            }} from {json.dumps(WEB_MODULE_PATH.as_uri())};
            let state = {{}};
            const stateHistory = {json.dumps(blocks)}.map((block) => {{
              state = applySfxBlockToChannelState(state, block);
              return state;
            }});
            process.stdout.write(JSON.stringify({{
              transports: {json.dumps(scenarios)}.map(sanitizeSfxTransport),
              stops: {json.dumps(stops)}.map(sanitizeSfxStop),
              stateHistory,
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
        self.assertEqual(payload["transports"], [sanitize_sfx_transport(item) for item in scenarios])
        self.assertEqual(payload["stops"], [sanitize_sfx_stop(item) for item in stops])
        state: dict = {}
        expected_history = []
        for block in blocks:
            state = apply_sfx_block_to_channel_state(state, block)
            expected_history.append(state)
        self.assertEqual(payload["stateHistory"], expected_history)

    def test_renpy_js_and_python_emit_the_same_stoppable_channel_commands(self) -> None:
        blocks = [
            {
                "type": "sfx_play",
                "assetId": "rain.ogg",
                "channelId": "ambience",
                "loop": True,
                "restartMode": "continue",
                "volume": 65,
                "fadeInMs": 1200,
                "replaceFadeOutMs": 800,
            },
            {
                "type": "sfx_play",
                "assetId": "click.ogg",
                "channelId": "effect",
                "loop": False,
                "volume": 80,
            },
            {"type": "sfx_stop", "channelId": "ambience", "fadeOutMs": 600},
        ]
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(RENPY_MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorRenpyExporter;
            const blocks = {json.dumps(blocks)};
            process.stdout.write(JSON.stringify(blocks.map((block, blockIndex) =>
              tools.renderBlock(block, {{ assetMap: new Map(), blockIndex }})
            )));
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
        js_lines = json.loads(completed.stdout)
        context = {
            "assetMap": {},
            "characterMap": {},
            "variableMap": {},
            "warnings": [],
        }
        python_lines = [
            render_story_block(block, {**context, "blockIndex": block_index})
            for block_index, block in enumerate(blocks)
        ]
        self.assertEqual(js_lines, python_lines)
        self.assertEqual(
            js_lines[0],
            ['    play canvasia_ambience "rain.ogg" fadeout 0.8 fadein 1.2 loop if_changed volume 0.65'],
        )
        self.assertEqual(js_lines[1], ['    play canvasia_effect_2 "click.ogg" noloop volume 0.8'])
        self.assertEqual(js_lines[2][0], "    stop canvasia_ambience fadeout 0.6")

    def test_editor_runtime_export_and_packaging_surfaces_are_wired(self) -> None:
        editor = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")
        index = (ROOT_DIR / "prototype_editor" / "index.html").read_text(encoding="utf-8")
        player = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        native = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        runner = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")
        runtime_registry = (ROOT_DIR / "export_runtime_module_registry.py").read_text(encoding="utf-8")
        catalog = (ROOT_DIR / "prototype_editor" / "modules" / "story_block_catalog.js").read_text(encoding="utf-8")
        python_exporter = (ROOT_DIR / "renpy_export.py").read_text(encoding="utf-8")

        self.assertIn('from "./runtime_sfx_transport.js"', player)
        self.assertIn("createSfxTransportController", player)
        self.assertIn("const runtimeSfxTransportTools = window.CanvasiaRuntimeSfxTransport", editor)
        self.assertIn("const sfxTransportEditorTools = window.CanvasiaEditorSfxTransport", editor)
        self.assertIn("runtime_sfx_transport.js", index)
        self.assertIn("sfx_transport_editor.js", index)
        self.assertIn("NativeSfxTransportController", native)
        self.assertIn('"sfxTransportState"', native)
        self.assertIn('NATIVE_RUNTIME_SFX_TRANSPORT_NAME = "runtime_sfx_transport.py"', runner)
        self.assertIn('("SfxTransport", "runtime_sfx_transport.js")', runtime_registry)
        self.assertIn('build_export_runtime_module_manifest("playerRuntime")', runner)
        self.assertIn('build_export_runtime_module_manifest("appRuntime", "app")', runner)
        self.assertIn('type: "sfx_stop"', catalog)
        self.assertIn("renpy.music.register_channel", python_exporter)


if __name__ == "__main__":
    unittest.main()
