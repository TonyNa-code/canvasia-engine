from __future__ import annotations

import unittest

from native_runtime.runtime_text_history import (
    append_text_history_entry,
    build_text_history_entry,
    build_text_history_key,
    collect_text_history_speakers,
    filter_text_history_entries,
    get_text_history_window,
    move_text_history_selection,
    normalize_text_history_query,
)


def make_entry(
    index: int,
    *,
    scene: str = "教室",
    speaker: str = "Alice",
    text: str = "早上好",
    voice: str = "",
) -> dict:
    entry = build_text_history_entry(
        scene_id=f"scene-{index}",
        block_index=index,
        block_type="dialogue",
        scene_name=scene,
        speaker_name=speaker,
        text=text,
        voice_asset_id=voice,
        voice_volume=120,
        voice_profile_id="profile-a",
    )
    assert entry is not None
    return entry


class NativeRuntimeTextHistoryTests(unittest.TestCase):
    def test_key_and_entry_building_are_stable_and_bounded(self) -> None:
        first = build_text_history_key("scene-a", 3, "dialogue", "你好")
        second = build_text_history_key("scene-a", 3, "dialogue", "你好")
        entry = make_entry(3, voice="voice-a")

        self.assertEqual(first, second)
        self.assertEqual(entry["voiceVolume"], 100)
        self.assertEqual(entry["voiceAssetId"], "voice-a")
        self.assertIsNone(build_text_history_entry(
            scene_id="scene-a",
            block_index=0,
            block_type="dialogue",
            scene_name="教室",
            speaker_name="Alice",
            text="  ",
        ))

    def test_append_deduplicates_and_enforces_limit(self) -> None:
        entries: list[dict] = []
        for index in range(5):
            entries = append_text_history_entry(entries, make_entry(index), limit=3)
        entries = append_text_history_entry(entries, entries[-1], limit=3)

        self.assertEqual(len(entries), 3)
        self.assertEqual([item["sceneName"] for item in entries], ["教室"] * 3)
        self.assertTrue(entries[0]["key"].startswith("scene-2:"))

    def test_unicode_search_speaker_and_voice_filters_preserve_indices(self) -> None:
        entries = [
            make_entry(0, text="ＡＢＣ计划"),
            make_entry(1, scene="屋顶", speaker="Bob", text="一起回家", voice="voice-b"),
            make_entry(2, scene="屋顶", speaker="Alice", text=f"{'很长的铺垫' * 30}终点关键词"),
        ]

        self.assertEqual(normalize_text_history_query(" abc "), "abc")
        self.assertEqual(collect_text_history_speakers(entries), ["Alice", "Bob"])
        self.assertEqual([index for index, _item in filter_text_history_entries(entries, query="abc")], [0])
        self.assertEqual([index for index, _item in filter_text_history_entries(entries, query="屋顶")], [1, 2])
        self.assertEqual([index for index, _item in filter_text_history_entries(entries, query="终点关键词")], [2])
        self.assertEqual([index for index, _item in filter_text_history_entries(entries, speaker="Bob")], [1])
        self.assertEqual([index for index, _item in filter_text_history_entries(entries, voiced_only=True)], [1])

    def test_selection_moves_inside_filtered_results_and_windows_around_selection(self) -> None:
        entries = [make_entry(index, speaker="Alice" if index % 2 == 0 else "Bob") for index in range(8)]
        filtered = filter_text_history_entries(entries, speaker="Alice")

        self.assertEqual(move_text_history_selection(filtered, 6, -2), 2)
        self.assertEqual(move_text_history_selection(filtered, 2, 99), 6)
        self.assertEqual([index for index, _item in get_text_history_window(filtered, 4, 2)], [2, 4])
        self.assertEqual(get_text_history_window([], 0, 4), [])


if __name__ == "__main__":
    unittest.main()
