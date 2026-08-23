from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_video_transport import sanitize_video_transport
from renpy_export import build_video_playback_spec


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_video_transport.js"
RENPY_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "renpy_exporter.js"


class VideoTransportContractTests(unittest.TestCase):
    def test_web_and_native_normalization_stays_aligned(self) -> None:
        scenarios = [
            {},
            {
                "autoplay": False,
                "loop": False,
                "resumeMode": "resume",
                "startTimeSeconds": 2.3456,
                "endTimeSeconds": 12,
                "fit": "cover",
                "volume": 60,
                "skippable": False,
            },
            {"loop": True, "skippable": False, "fit": "fill", "volume": 0},
            {"volume": None},
            {"volume": 40.5},
            {"startTimeSeconds": 9, "endTimeSeconds": 4, "resumeMode": "broken", "fit": "broken"},
        ]
        script = textwrap.dedent(
            f"""
            import {{ sanitizeVideoTransport }} from {json.dumps(WEB_MODULE_PATH.as_uri())};
            process.stdout.write(JSON.stringify({json.dumps(scenarios)}.map(sanitizeVideoTransport)));
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
        self.assertEqual(json.loads(completed.stdout), [sanitize_video_transport(item) for item in scenarios])

    def test_renpy_exporters_keep_timing_and_flag_advanced_transport_rules(self) -> None:
        block = {
            "autoplay": False,
            "loop": True,
            "resumeMode": "resume",
            "startTimeSeconds": 2,
            "endTimeSeconds": 12,
            "volume": 60,
        }
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(RENPY_MODULE_PATH))}, "utf8"), context);
            const warnings = [];
            const spec = context.window.CanvasiaEditorRenpyExporter.buildVideoPlaybackSpec(
              "video/op.webm",
              {json.dumps(block)},
              {{ warnings, sceneId: "scene_video", blockIndex: 2 }}
            );
            process.stdout.write(JSON.stringify({{ spec, warnings }}));
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
        python_context = {"warnings": [], "sceneId": "scene_video", "blockIndex": 2}
        self.assertEqual(payload["spec"], build_video_playback_spec("video/op.webm", block, python_context))
        self.assertEqual(payload["warnings"], python_context["warnings"])
        self.assertEqual(payload["spec"]["path"], "<from 2 to 12 volume 0.6>video/op.webm")
        self.assertEqual(payload["warnings"][0]["code"], "renpy_video_transport_review")

    def test_editor_web_native_and_export_surfaces_are_wired(self) -> None:
        editor = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")
        editor_html = (ROOT_DIR / "prototype_editor" / "index.html").read_text(encoding="utf-8")
        player = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        native = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        runner = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")
        runtime_registry = (ROOT_DIR / "export_runtime_module_registry.py").read_text(encoding="utf-8")

        self.assertIn('from "./runtime_video_transport.js"', player)
        self.assertIn("bindVideoTransportToVideo", player)
        self.assertIn("videoPlaybackPositionSeconds", player)
        self.assertIn("const runtimeVideoTransportTools = window.CanvasiaRuntimeVideoTransport", editor)
        self.assertIn("createPreviewVideoController", editor)
        self.assertIn("capturePreviewCurrentVideoPlaybackPosition", editor)
        self.assertIn("runtime_video_transport.js", editor_html)
        self.assertIn("video_transport_editor.js", editor_html)
        self.assertIn("build_native_video_line", native)
        self.assertIn("can_open_external_video,", native)
        self.assertIn("get_external_video_opener_label,", native)
        self.assertIn("is_optional_python_module_available,", native)
        self.assertIn("get_current_video_playback_position", native)
        self.assertIn("currentVideoPlaybackPositionSeconds", native)
        self.assertIn('NATIVE_RUNTIME_VIDEO_TRANSPORT_NAME = "runtime_video_transport.py"', runner)
        self.assertIn('("VideoTransport", "runtime_video_transport.js")', runtime_registry)
        self.assertIn('build_export_runtime_module_manifest("playerRuntime")', runner)
        self.assertIn('build_export_runtime_module_manifest("appRuntime", "app")', runner)


if __name__ == "__main__":
    unittest.main()
