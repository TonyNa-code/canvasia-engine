from __future__ import annotations

import unittest
from pathlib import Path

from native_runtime.runtime_video_transport import (
    NATIVE_VIDEO_BACKEND_OPTIONS,
    NATIVE_VIDEO_EMBEDDED_BACKEND_ID,
    NATIVE_VIDEO_SYNC_BACKEND_ID,
    build_native_video_line,
    build_video_clip_label,
    can_open_external_video,
    get_external_video_opener_label,
    get_video_initial_position,
    get_video_playback_position,
    get_video_preview_cache_key,
    sanitize_video_transport,
)


class NativeRuntimeVideoTransportTests(unittest.TestCase):
    def test_transport_defaults_preserve_legacy_video_behavior(self) -> None:
        self.assertEqual(
            sanitize_video_transport(),
            {
                "autoplay": True,
                "loop": False,
                "resumeMode": "restart",
                "startTimeSeconds": 0.0,
                "endTimeSeconds": 0.0,
                "fit": "contain",
                "volume": 100,
                "skippable": True,
            },
        )
        invalid = sanitize_video_transport(
            {"startTimeSeconds": 8, "endTimeSeconds": 4, "fit": "broken", "volume": 400}
        )
        self.assertEqual(invalid["endTimeSeconds"], 0)
        self.assertEqual(invalid["fit"], "contain")
        self.assertEqual(invalid["volume"], 100)
        self.assertTrue(sanitize_video_transport({"loop": True, "skippable": False})["skippable"])

    def test_resume_position_and_playback_position_are_bounded(self) -> None:
        transport = {
            "resumeMode": "resume",
            "startTimeSeconds": 2,
            "endTimeSeconds": 9,
        }
        self.assertEqual(get_video_initial_position(transport, 6.25), 6.25)
        self.assertEqual(get_video_initial_position(transport, 10), 2)
        self.assertEqual(get_video_initial_position(transport, {"corrupted": True}), 2)
        self.assertEqual(get_video_initial_position({**transport, "resumeMode": "restart"}, 6.25), 2)

        class Playback:
            elapsed_ms = 7125

        self.assertEqual(get_video_playback_position(Playback()), 7.125)
        self.assertEqual(get_video_playback_position(None, 3.5), 3.5)

    def test_native_line_contains_complete_transport_contract(self) -> None:
        asset_path = Path("/tmp/opening.mp4")
        line = build_native_video_line(
            {
                "assetId": "video-op",
                "title": "Opening",
                "autoplay": False,
                "loop": True,
                "resumeMode": "resume",
                "startTimeSeconds": 2,
                "endTimeSeconds": 12,
                "fit": "fill",
                "volume": 40,
                "skippable": False,
            },
            {"name": "OP"},
            asset_path,
            preview_mode="embedded",
            block_label="播放视频",
            resume_time_seconds=6,
        )
        self.assertEqual(line["videoPlaybackPositionSeconds"], 6)
        self.assertEqual(line["videoClipLabel"], "2 秒 → 12 秒")
        self.assertEqual(line["videoFit"], "fill")
        self.assertEqual(line["videoVolume"], 40)
        self.assertFalse(line["videoAutoplay"])
        self.assertTrue(line["videoLoop"])
        self.assertTrue(line["videoSkippable"])
        self.assertIn("循环播放", line["text"])
        self.assertEqual(get_video_preview_cache_key(line), f"{asset_path.resolve()}::6.000")
        self.assertEqual(build_video_clip_label(0, 0), "开头 → 自然结尾")

    def test_backend_registry_keeps_sync_and_visual_fallbacks_explicit(self) -> None:
        options = {item["id"]: item for item in NATIVE_VIDEO_BACKEND_OPTIONS}
        self.assertTrue(options[NATIVE_VIDEO_SYNC_BACKEND_ID]["audio"])
        self.assertTrue(options[NATIVE_VIDEO_SYNC_BACKEND_ID]["embeddedVideo"])
        self.assertFalse(options[NATIVE_VIDEO_EMBEDDED_BACKEND_ID]["audio"])
        self.assertTrue(options[NATIVE_VIDEO_EMBEDDED_BACKEND_ID]["embeddedVideo"])

    def test_system_video_opener_contract_is_safe_to_query(self) -> None:
        self.assertIsInstance(can_open_external_video(), bool)
        self.assertTrue(get_external_video_opener_label())


if __name__ == "__main__":
    unittest.main()
