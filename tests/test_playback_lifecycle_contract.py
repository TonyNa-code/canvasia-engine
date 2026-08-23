from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class PlaybackLifecycleContractTests(unittest.TestCase):
    def test_editor_web_native_and_export_surfaces_share_the_lifecycle_boundary(self) -> None:
        editor = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")
        editor_html = (ROOT_DIR / "prototype_editor" / "index.html").read_text(encoding="utf-8")
        module_guard = (ROOT_DIR / "prototype_editor" / "modules" / "module_guard.js").read_text(
            encoding="utf-8"
        )
        player = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        player_css = (ROOT_DIR / "export_player_template" / "player.css").read_text(encoding="utf-8")
        native = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        runner = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")
        runtime_registry = (ROOT_DIR / "export_runtime_module_registry.py").read_text(encoding="utf-8")

        self.assertIn('from "./runtime_playback_lifecycle.js"', player)
        self.assertIn("createDocumentPlaybackLifecycle", player)
        self.assertIn("runtimeAutoAdvanceDelayController", player)
        self.assertIn("runtimeVideoFallbackDelayController", player)
        self.assertIn("runtimeCreditsDelayController", player)
        self.assertNotIn("let autoAdvanceTimer", player)
        self.assertIn('data-playback-paused="true"', player_css)
        self.assertIn("animation-play-state: paused", player_css)

        self.assertIn("const runtimePlaybackLifecycleTools = window.CanvasiaRuntimePlaybackLifecycle", editor)
        self.assertIn("previewAutoAdvanceDelayController", editor)
        self.assertIn("previewPlaybackLifecycle", editor)
        self.assertNotIn("let previewAutoAdvanceTimer", editor)
        self.assertIn("runtime_playback_lifecycle.js", editor_html)
        self.assertIn("CanvasiaRuntimePlaybackLifecycle", module_guard)

        self.assertIn("NativePlaybackLifecycleController", native)
        self.assertIn("sync_runtime_playback_lifecycle", native)
        self.assertIn("shift_runtime_playback_timestamps", native)
        self.assertIn("get_target_fps", native)
        self.assertIn('NATIVE_RUNTIME_PLAYBACK_LIFECYCLE_NAME = "runtime_playback_lifecycle.py"', runner)
        self.assertIn('("PlaybackLifecycle", "runtime_playback_lifecycle.js")', runtime_registry)


if __name__ == "__main__":
    unittest.main()
