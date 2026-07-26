from __future__ import annotations

import unittest

from native_runtime.runtime_achievements import (
    build_native_achievement_archive_entries,
    collect_custom_achievement_definitions,
    get_custom_achievement_storage_id,
    get_safe_achievement_author_id,
    sanitize_achievement_unlock_block,
)


class NativeRuntimeAchievementsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chapters = [
            {
                "scenes": [
                    {
                        "id": "secret-room",
                        "blocks": [
                            {
                                "id": "unlock-1",
                                "type": "achievement_unlock",
                                "achievementId": " First Meet! ",
                                "title": "初次相遇",
                                "description": "见到她。",
                                "category": "隐藏路线",
                                "requirement": "进入秘密房间",
                                "hiddenBeforeUnlock": True,
                                "iconAssetId": "icon-1",
                            },
                            {
                                "id": "unlock-2",
                                "type": "achievement_unlock",
                                "achievementId": "first meet",
                                "title": "重复定义",
                            },
                        ],
                    }
                ]
            }
        ]

    def test_ids_and_duplicate_definitions_match_web_contract(self) -> None:
        self.assertEqual(get_safe_achievement_author_id("  First Meet! "), "first-meet")
        self.assertEqual(get_custom_achievement_storage_id("秘密 成就"), "custom:秘密-成就")
        sanitized = sanitize_achievement_unlock_block(self.chapters[0]["scenes"][0]["blocks"][0])
        self.assertEqual(sanitized["id"], "custom:first-meet")
        definitions = collect_custom_achievement_definitions(self.chapters)
        self.assertEqual(len(definitions), 1)
        self.assertEqual(definitions[0]["duplicateCount"], 1)

    def test_archive_entries_hide_details_until_unlock(self) -> None:
        locked = build_native_achievement_archive_entries(
            self.chapters,
            metrics={"hasScenes": True, "characterCount": 1, "unlockedCharacterCount": 0},
        )
        custom_locked = locked[0]
        self.assertEqual(custom_locked["name"], "隐藏成就")
        self.assertEqual(custom_locked["previewAssetId"], "")
        self.assertFalse(custom_locked["actionEnabled"])
        unlocked = build_native_achievement_archive_entries(
            self.chapters,
            metrics={"hasScenes": True},
            unlocked_custom_ids=["custom:first-meet"],
        )
        custom_unlocked = unlocked[0]
        self.assertEqual(custom_unlocked["name"], "初次相遇")
        self.assertEqual(custom_unlocked["previewAssetId"], "icon-1")
        self.assertTrue(custom_unlocked["actionEnabled"])
        self.assertEqual(unlocked[1]["id"], "first_start")


if __name__ == "__main__":
    unittest.main()
