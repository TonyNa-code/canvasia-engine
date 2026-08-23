from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from native_runtime.runtime_dialog_panel import build_dialog_panel_render_plan


ROOT_DIR = Path(__file__).resolve().parents[1]


class FakeArt:
    def __init__(self, size: tuple[int, int]) -> None:
        self.size = size

    def get_size(self) -> tuple[int, int]:
        return self.size


class NativeRuntimeDialogPanelTests(unittest.TestCase):
    def build_runtime(self, config: dict) -> SimpleNamespace:
        art = FakeArt((320, 180))
        return SimpleNamespace(
            dialog_box_config=config,
            get_dialog_border_radius=lambda _height: 24,
            scale_dialog_opacity=lambda value: round(value * 0.8),
            _load_image=lambda asset_id: art if asset_id == "panel_art" else None,
        )

    def test_render_plan_is_position_independent_and_style_sensitive(self) -> None:
        runtime = self.build_runtime(
            {
                "backgroundColor": (12, 18, 30),
                "backgroundOpacity": 200,
                "borderColor": (90, 150, 240),
                "borderOpacity": 72,
                "borderWidth": 2,
                "shadowStrength": 18,
                "panelAssetId": "panel_art",
                "panelAssetOpacity": 60,
                "panelAssetFit": "contain",
            }
        )
        first_rect = SimpleNamespace(width=900, height=240, size=(900, 240), left=80, top=420, topleft=(80, 420))
        moved_rect = SimpleNamespace(width=900, height=240, size=(900, 240), left=110, top=390, topleft=(110, 390))

        first = build_dialog_panel_render_plan(runtime, first_rect)
        moved = build_dialog_panel_render_plan(runtime, moved_rect)

        self.assertEqual(first["cacheKey"], moved["cacheKey"])
        self.assertNotEqual(first["surfacePosition"], moved["surfacePosition"])
        self.assertEqual(first["surfaceSize"], (932, 272))
        self.assertEqual(first["panelOrigin"], (16, 8))
        self.assertEqual(first["backgroundOpacity"], 160)
        self.assertEqual(first["panelArtOpacity"], 48)

        runtime.dialog_box_config["backgroundOpacity"] = 120
        changed = build_dialog_panel_render_plan(runtime, first_rect)
        self.assertNotEqual(first["cacheKey"], changed["cacheKey"])

    def test_player_delegates_panel_chrome_and_exporter_bundles_module(self) -> None:
        player = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        exporter = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")

        self.assertIn("from .runtime_dialog_panel import render_runtime_dialog_panel", player)
        self.assertIn("render_runtime_dialog_panel(self, rect)", player)
        self.assertIn('NATIVE_RUNTIME_DIALOG_PANEL_NAME = "runtime_dialog_panel.py"', exporter)
        self.assertIn("NATIVE_RUNTIME_DIALOG_PANEL_NAME,", exporter)


if __name__ == "__main__":
    unittest.main()
