from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_music_transport import sanitize_music_transport
from renpy_export import build_music_playback_spec


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_music_transport.js"
RENPY_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "renpy_exporter.js"


class MusicTransportContractTests(unittest.TestCase):
    def test_web_and_native_normalization_stays_aligned(self) -> None:
        scenarios = [
            {},
            {"loop": False, "startTimeSeconds": 2.3456, "restartMode": "restart"},
            {"loop": True, "startTimeSeconds": 1, "loopStartSeconds": 8, "loopEndSeconds": 15},
            {"loopStartSeconds": 9, "loopEndSeconds": 4, "restartMode": "broken"},
        ]
        script = textwrap.dedent(
            f"""
            import {{ sanitizeMusicTransport }} from {json.dumps(WEB_MODULE_PATH.as_uri())};
            process.stdout.write(JSON.stringify({json.dumps(scenarios)}.map(sanitizeMusicTransport)));
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
        self.assertEqual(json.loads(completed.stdout), [sanitize_music_transport(item) for item in scenarios])

    def test_renpy_js_and_python_emit_the_same_partial_playback_spec(self) -> None:
        block = {
            "loop": True,
            "startTimeSeconds": 2,
            "loopStartSeconds": 8,
            "loopEndSeconds": 15,
            "restartMode": "continue",
        }
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(RENPY_MODULE_PATH))}, "utf8"), context);
            process.stdout.write(JSON.stringify(
              context.window.CanvasiaEditorRenpyExporter.buildMusicPlaybackSpec("audio/theme.ogg", {json.dumps(block)})
            ));
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
        expected = build_music_playback_spec("audio/theme.ogg", block)
        self.assertEqual(json.loads(completed.stdout), expected)
        self.assertEqual(expected["path"], "<from 2 to 15 loop 8>audio/theme.ogg")
        self.assertEqual(expected["restartClause"], " if_changed")

    def test_all_runtime_and_export_surfaces_are_wired(self) -> None:
        editor = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")
        player = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        native = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        runner = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")
        runtime_registry = (ROOT_DIR / "export_runtime_module_registry.py").read_text(encoding="utf-8")

        self.assertIn('from "./runtime_music_transport.js"', player)
        self.assertIn("const runtimeMusicTransportTools = window.CanvasiaRuntimeMusicTransport", editor)
        self.assertIn("bindMusicTransportToAudio", player)
        self.assertIn("bindMusicTransportToAudio", editor)
        self.assertIn("currentMusicCueId", player)
        self.assertIn("previewCurrentMusicCueId", editor)
        self.assertIn("keepExistingMusicPlaybackAlive", player)
        self.assertIn("keepExistingMusicPlaybackAlive", editor)
        web_sync_audio = player.split("function syncAudio(snapshot)", 1)[1].split("function getRuntimeMusicTargetVolume", 1)[0]
        editor_sync_audio = editor.split("function syncPreviewMusic(snapshot)", 1)[1].split("function getPreviewMusicTargetVolume", 1)[0]
        self.assertNotIn("audio.loop = true;", web_sync_audio)
        self.assertNotIn("audio.loop = true;", editor_sync_audio)
        self.assertIn("NativeMusicTransportController", native)
        self.assertIn("is_new_cue", native)
        self.assertIn('NATIVE_RUNTIME_MUSIC_TRANSPORT_NAME = "runtime_music_transport.py"', runner)
        self.assertIn('("MusicTransport", "runtime_music_transport.js")', runtime_registry)


if __name__ == "__main__":
    unittest.main()
