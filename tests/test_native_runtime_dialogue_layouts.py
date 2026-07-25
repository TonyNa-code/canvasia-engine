from __future__ import annotations

import unittest

from native_runtime.runtime_dialogue_layouts import (
    DIALOGUE_LAYOUT_IDS,
    build_dialogue_layout_presentation,
    collect_nvl_page_entries,
    get_dialogue_layout_from_block,
    get_safe_dialogue_layout,
    should_start_new_nvl_page,
)


class NativeRuntimeDialogueLayoutsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.blocks = [
            {"id": "adv", "type": "dialogue", "text": "经典", "dialogueLayout": "adv"},
            {
                "id": "nvl_1",
                "type": "narration",
                "text": "第一句",
                "dialogueLayout": "nvl",
                "nvlPageBreak": True,
            },
            {"id": "effect", "type": "screen_shake"},
            {
                "id": "nvl_2",
                "type": "dialogue",
                "speakerId": "hero",
                "text": "第二句",
                "dialogueLayout": "nvl",
            },
            {"id": "nvl_3", "type": "narration", "text": "第三句", "dialogueLayout": "nvl"},
            {"id": "choice", "type": "choice"},
            {"id": "nvl_4", "type": "narration", "text": "新段", "dialogueLayout": "nvl"},
        ]

    def test_sanitizes_layout_and_ignores_non_dialogue_blocks(self) -> None:
        self.assertEqual(DIALOGUE_LAYOUT_IDS, ("adv", "nvl", "cinematic"))
        self.assertEqual(get_safe_dialogue_layout("unknown"), "adv")
        self.assertEqual(get_dialogue_layout_from_block({"type": "choice", "dialogueLayout": "nvl"}), "adv")
        self.assertTrue(should_start_new_nvl_page(self.blocks[1]))

    def test_collects_current_nvl_page_across_visual_effects(self) -> None:
        entries = collect_nvl_page_entries(
            self.blocks,
            4,
            resolve_entry=lambda block, index: {
                "id": block["id"],
                "blockIndex": index,
                "type": block["type"],
                "speakerName": "主人公" if block.get("speakerId") == "hero" else "",
                "text": block["text"],
            },
        )

        self.assertEqual([entry["id"] for entry in entries], ["nvl_1", "nvl_2", "nvl_3"])
        self.assertEqual(entries[1]["speakerName"], "主人公")
        self.assertEqual(
            [entry["id"] for entry in collect_nvl_page_entries(self.blocks, 6)],
            ["nvl_4"],
        )

    def test_builds_layout_presentation_with_page_metadata(self) -> None:
        presentation = build_dialogue_layout_presentation(
            self.blocks[1],
            blocks=self.blocks,
            current_index=1,
        )

        self.assertEqual(presentation["layout"], "nvl")
        self.assertTrue(presentation["startsNewPage"])
        self.assertEqual([entry["id"] for entry in presentation["entries"]], ["nvl_1"])
        self.assertIn("NVL", presentation["label"])


if __name__ == "__main__":
    unittest.main()
