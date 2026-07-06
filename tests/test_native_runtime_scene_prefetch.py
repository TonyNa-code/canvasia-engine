from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from native_runtime.runtime_player import NativeRuntimePlayer
from native_runtime.runtime_scene_prefetch import (
    build_runtime_scene_prefetch_manifest,
    build_runtime_scene_prefetch_snapshot,
    get_runtime_scene_prefetch_summary,
)


def build_prefetch_fixture() -> dict:
    assets_by_id = {
        "bg_next": {"id": "bg_next", "name": "Next BG", "type": "background", "exportUrl": "assets/bg_next.png", "fileSizeBytes": 1024},
        "sfx_click": {"id": "sfx_click", "name": "Click", "type": "sfx", "exportUrl": "assets/click.wav", "fileSizeBytes": 256},
        "branch_bg": {"id": "branch_bg", "name": "Branch BG", "type": "background", "exportUrl": "assets/branch.png", "fileSizeBytes": 2048},
        "branch_voice": {"id": "branch_voice", "name": "Branch Voice", "type": "voice", "exportUrl": "assets/branch_voice.wav", "fileSizeBytes": 512},
        "hero_angry": {"id": "hero_angry", "name": "Hero Angry", "type": "sprite", "exportUrl": "assets/hero_angry.png", "fileSizeBytes": 4096},
        "branch_video": {"id": "branch_video", "name": "Branch Video", "type": "video", "exportUrl": "assets/branch.mp4", "fileSizeBytes": 8192},
        "missing_bg": {"id": "missing_bg", "name": "Missing BG", "type": "background", "exportUrl": "", "isMissing": True},
    }
    characters_by_id = {
        "hero": {
            "id": "hero",
            "expressions": [
                {"id": "neutral", "spriteAssetId": "missing_bg"},
                {"id": "angry", "spriteAssetId": "hero_angry"},
            ],
        }
    }
    scenes_by_id = {
        "intro": {
            "id": "intro",
            "blocks": [
                {"id": "b0", "type": "dialogue", "speakerId": "hero", "expressionId": "neutral", "text": "Hello"},
                {"id": "b1", "type": "choice", "options": [{"text": "Branch", "gotoSceneId": "branch"}]},
                {"id": "b2", "type": "background", "assetId": "bg_next"},
                {"id": "b3", "type": "sfx_play", "assetId": "sfx_click"},
            ],
        },
        "branch": {
            "id": "branch",
            "blocks": [
                {"id": "c0", "type": "background", "assetId": "branch_bg"},
                {"id": "c1", "type": "dialogue", "speakerId": "hero", "expressionId": "angry", "voiceAssetId": "branch_voice", "text": "Route"},
                {"id": "c2", "type": "video_play", "assetId": "branch_video"},
            ],
        },
    }
    return {
        "assetsById": assets_by_id,
        "charactersById": characters_by_id,
        "scenesById": scenes_by_id,
    }


class NativeRuntimeScenePrefetchTests(unittest.TestCase):
    def test_scene_prefetch_manifest_collects_upcoming_blocks_and_choice_routes(self) -> None:
        fixture = build_prefetch_fixture()
        snapshot = build_runtime_scene_prefetch_snapshot(
            fixture["scenesById"]["intro"],
            1,
            scene_id="intro",
            choice_options=[{"text": "Branch", "gotoSceneId": "branch"}],
        )

        manifest = build_runtime_scene_prefetch_manifest(
            snapshot,
            fixture,
            {"blockLookahead": 4, "targetBlockLookahead": 6, "maxEntries": 16},
        )
        asset_ids = [entry["assetId"] for entry in manifest["entries"]]
        summary = get_runtime_scene_prefetch_summary(manifest)

        self.assertEqual(manifest["generatedBy"], "runtime_scene_prefetch")
        self.assertEqual(manifest["entrySceneId"], "intro")
        self.assertEqual(manifest["targetSceneIds"], ["branch"])
        self.assertIn("intro:b1:1", manifest["prefetchKey"])
        self.assertEqual(asset_ids[:2], ["bg_next", "sfx_click"])
        self.assertIn("branch_bg", asset_ids)
        self.assertIn("branch_voice", asset_ids)
        self.assertIn("hero_angry", asset_ids)
        self.assertIn("branch_video", asset_ids)
        self.assertNotIn("missing_bg", asset_ids)
        self.assertEqual(summary["totalCount"], len(asset_ids))
        self.assertEqual(summary["imageCount"], 3)
        self.assertEqual(summary["audioCount"], 2)
        self.assertEqual(summary["videoCount"], 1)

    def test_native_player_scene_prefetch_warms_assets_without_window(self) -> None:
        fixture = build_prefetch_fixture()
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir)
            for asset in fixture["assetsById"].values():
                export_url = str(asset.get("exportUrl") or "")
                if not export_url:
                    continue
                path = bundle_dir / export_url
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"asset")

            class FakeMixer:
                def get_init(self) -> bool:
                    return True

            class FakePygame:
                mixer = FakeMixer()

            player = NativeRuntimePlayer.__new__(NativeRuntimePlayer)
            player.bundle_dir = bundle_dir
            player.pygame = FakePygame()
            player.project = {"runtimeSettings": {"performanceProfile": "high_quality_pc"}}
            player.assets_by_id = fixture["assetsById"]
            player.characters_by_id = fixture["charactersById"]
            player.scenes_by_id = fixture["scenesById"]
            player.current_scene_id = "intro"
            player.current_block_index = 1
            player.current_choices = [{"text": "Branch", "gotoSceneId": "branch"}]
            player.finished = False
            player.title_screen_active = False
            player.image_cache = {}
            player.sound_cache = {}
            player.runtime_preload_finished_asset_ids = set()
            player.runtime_scene_prefetch_manifest = {}
            player.runtime_scene_prefetch_key = ""
            player.runtime_scene_prefetch_entries = []
            player.runtime_scene_prefetch_pending_entries = []
            player.runtime_scene_prefetch_finished_asset_ids = set()
            player.runtime_scene_prefetched_asset_ids = set()
            player.runtime_scene_prefetch_status = {}
            player.current_bgm_asset_id = None

            def fake_load_image(asset_id: str | None):
                player.image_cache[asset_id] = f"image:{asset_id}"
                return player.image_cache[asset_id]

            def fake_load_sound(asset_id: str | None):
                player.sound_cache[asset_id] = f"sound:{asset_id}"
                return player.sound_cache[asset_id]

            player._load_image = fake_load_image
            player._load_sound = fake_load_sound

            player.update_runtime_scene_prefetch_queue(max_entries=24)

        status = player.runtime_scene_prefetch_status
        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["totalEntries"], 6)
        self.assertEqual(status["loadedEntries"], 6)
        self.assertEqual(status["pendingEntries"], 0)
        self.assertIn("bg_next", player.image_cache)
        self.assertIn("branch_bg", player.image_cache)
        self.assertIn("hero_angry", player.image_cache)
        self.assertIn("sfx_click", player.sound_cache)
        self.assertIn("branch_voice", player.sound_cache)
        self.assertIn("branch_video", player.runtime_scene_prefetched_asset_ids)
        self.assertIn("已准备 6/6 项", player.get_runtime_scene_prefetch_status_line())


if __name__ == "__main__":
    unittest.main()
