from __future__ import annotations

import unittest

from editor_asset_usage import BLOCK_LABELS, collect_asset_usages_from_bundle


class EditorAssetUsageTests(unittest.TestCase):
    def test_asset_usage_tracks_character_motion_voice_and_story_assets(self) -> None:
        bundle = {
            "characters": {
                "characters": [
                    {
                        "id": "heroine",
                        "displayName": "夏音",
                        "defaultSpriteId": "sprite_default",
                        "expressions": [
                            {"id": "default", "name": "默认", "spriteAssetId": "sprite_default"},
                            {"id": "smile", "name": "微笑", "spriteAssetId": "sprite_smile"},
                        ],
                    }
                ]
            },
            "chapters": [
                {
                    "scenes": [
                        {
                            "id": "scene_1",
                            "name": "天台",
                            "blocks": [
                                {"type": "background", "assetId": "bg_rooftop"},
                                {
                                    "type": "dialogue",
                                    "speakerId": "heroine",
                                    "expressionId": "default",
                                    "voiceAssetId": "voice_001",
                                },
                                {
                                    "type": "character_move",
                                    "characterId": "heroine",
                                    "expressionId": "smile",
                                },
                            ],
                        }
                    ]
                }
            ],
        }

        def collect_presentation(character: dict):
            self.assertEqual(character["id"], "heroine")
            return [
                ("live2d_model", "Live2D 模型入口"),
                ("layer_eye", "差分图层：眼睛"),
            ]

        self.assertIn(
            "场景：天台 / 夏音 微笑",
            collect_asset_usages_from_bundle("sprite_smile", bundle, collect_presentation),
        )
        self.assertEqual(BLOCK_LABELS["character_move"], "角色动作")
        self.assertIn(
            "场景：天台 / 台词语音",
            collect_asset_usages_from_bundle("voice_001", bundle, collect_presentation),
        )
        self.assertIn(
            "场景：天台 / 切换背景",
            collect_asset_usages_from_bundle("bg_rooftop", bundle, collect_presentation),
        )
        self.assertIn(
            "角色Live2D 模型入口：夏音",
            collect_asset_usages_from_bundle("live2d_model", bundle, collect_presentation),
        )
        self.assertIn(
            "角色差分图层：夏音 / 眼睛",
            collect_asset_usages_from_bundle("layer_eye", bundle, collect_presentation),
        )

    def test_asset_usage_handles_incomplete_bundle_without_crashing(self) -> None:
        self.assertEqual(collect_asset_usages_from_bundle("asset", None, lambda _character: []), [])
        self.assertEqual(collect_asset_usages_from_bundle("", {"chapters": []}, lambda _character: []), [])
        self.assertEqual(
            collect_asset_usages_from_bundle(
                "asset",
                {"characters": {"characters": [None]}, "chapters": [None]},
                lambda _character: [],
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
