from __future__ import annotations

import unittest

from native_runtime.runtime_player_view import (
    MAX_FORMAL_SAVE_SLOT_COUNT,
    build_save_dialog_page_data,
    build_video_clip_label,
    format_video_timestamp,
    get_project_dialog_box_config,
    get_project_formal_save_slot_count,
    get_project_game_ui_config,
    get_safe_audio_fade_ms,
    get_safe_character_stage,
    get_safe_transition_duration_ms,
    get_safe_volume_percent,
    wrap_text,
    ellipsize_text,
)


class DummyFont:
    def size(self, text: str) -> tuple[int, int]:
        return (len(str(text)) * 8, 18)


class NativeRuntimePlayerViewTests(unittest.TestCase):
    def test_project_view_config_is_safely_sanitized(self) -> None:
        project = {
            "runtimeSettings": {"formalSaveSlotCount": 999},
            "dialogBoxConfig": {
                "preset": "warm",
                "shape": "capsule",
                "widthPercent": 10,
                "backgroundColor": "#fffaf5",
                "backgroundOpacity": 160,
                "anchor": "free",
            },
            "gameUiConfig": {
                "preset": "custom",
                "layoutPreset": "cinematic",
                "fontFamily": "A" * 120,
                "panelOpacity": 10,
                "accentColor": "#79dcff",
                "buttonFrameSlice": {"top": 240, "right": -1, "bottom": 20, "left": 18},
            },
        }

        self.assertEqual(get_project_formal_save_slot_count(project), MAX_FORMAL_SAVE_SLOT_COUNT)
        dialog_box_config = get_project_dialog_box_config(project)
        self.assertEqual(dialog_box_config["preset"], "warm")
        self.assertEqual(dialog_box_config["shape"], "capsule")
        self.assertEqual(dialog_box_config["widthPercent"], 55)
        self.assertEqual(dialog_box_config["backgroundOpacity"], 100)
        self.assertEqual(dialog_box_config["anchor"], "free")

        game_ui_config = get_project_game_ui_config(project)
        self.assertEqual(game_ui_config["preset"], "custom")
        self.assertEqual(game_ui_config["layoutPreset"], "cinematic")
        self.assertEqual(len(game_ui_config["fontFamily"]), 80)
        self.assertEqual(game_ui_config["panelOpacity"], 35)
        self.assertEqual(game_ui_config["accentColor"], (121, 220, 255))
        self.assertEqual(game_ui_config["buttonFrameSlice"], {"top": 96, "right": 0, "bottom": 20, "left": 18})

    def test_save_dialog_summary_formats_variable_values(self) -> None:
        project = {"runtimeSettings": {"formalSaveSlotCount": 4}}
        save_store = {
            "quickSave": {
                "sceneName": "序章",
                "savedAt": "2026-07-15T09:10:11",
                "summaryText": "刚刚进入教室。",
                "variableState": {"affection": 2.0, "flag": True},
            },
            "formalSlots": [
                None,
                {
                    "sceneName": "屋顶",
                    "savedAt": "2026-07-15T10:20:30",
                    "summaryText": "",
                    "variableState": {"affection": 3.0, "flag": False},
                },
            ],
        }
        variables = [
            {"id": "affection", "name": "好感", "type": "number"},
            {"id": "flag", "name": "约定", "type": "boolean"},
        ]

        page_data = build_save_dialog_page_data(project, save_store, page=0, page_size=2, variables=variables)

        self.assertEqual(page_data["slotCount"], 4)
        self.assertEqual(page_data["pageCount"], 2)
        self.assertEqual(page_data["quickSave"]["savedAt"], "07-15 09:10")
        self.assertEqual(page_data["quickSave"]["variableSummaryText"], "好感:2 / 约定:开")
        self.assertTrue(page_data["visibleSlots"][0]["isEmpty"])
        self.assertEqual(page_data["visibleSlots"][1]["sceneName"], "屋顶")
        self.assertEqual(page_data["visibleSlots"][1]["summaryText"], "当前没有摘要。")
        self.assertEqual(page_data["visibleSlots"][1]["variableSummaryText"], "好感:3 / 约定:关")

    def test_timing_stage_and_text_helpers_have_safe_bounds(self) -> None:
        self.assertEqual(get_safe_audio_fade_ms(-50, 600), 0)
        self.assertEqual(get_safe_audio_fade_ms(999999, 600), 30000)
        self.assertEqual(get_safe_volume_percent(180), 100)
        self.assertEqual(get_safe_transition_duration_ms("bad", 720), 720)
        self.assertEqual(format_video_timestamp(63), "1:03")
        self.assertEqual(build_video_clip_label(12.5, 63), "0:12.5 -> 1:03")
        self.assertEqual(build_video_clip_label(0, 0), "整段播放")

        stage = get_safe_character_stage({"offsetX": 999, "offsetY": -999, "scale": 10, "opacity": 250, "layer": 99, "flipX": "yes"})
        self.assertEqual(stage, {"offsetX": 60, "offsetY": -45, "scale": 45, "opacity": 100, "layer": 10, "flipX": True})

        font = DummyFont()
        self.assertEqual(wrap_text(font, "Hello world", 44), ["Hello", "world"])
        self.assertEqual(ellipsize_text(font, "Hello world", 48), "Hello…")


if __name__ == "__main__":
    unittest.main()
