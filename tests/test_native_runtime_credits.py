from __future__ import annotations

import unittest

from native_runtime.runtime_credits import (
    build_native_credits_layout,
    build_native_credits_playback,
    can_advance_native_credits,
    get_native_credits_progress,
    is_native_credits_complete,
    sanitize_native_credits_block,
)


class NativeRuntimeCreditsTests(unittest.TestCase):
    def test_sanitize_credits_clamps_duration_and_keeps_author_rules(self) -> None:
        credits = sanitize_native_credits_block(
            {
                "title": "  TRUE END  ",
                "subtitle": "再见，夏天",
                "lines": ["企划：Creator", "", "音乐：Composer"],
                "durationSeconds": 999,
                "background": "light",
                "skippable": False,
            }
        )

        self.assertEqual(credits["title"], "TRUE END")
        self.assertEqual(credits["lines"], ["企划：Creator", "音乐：Composer"])
        self.assertEqual(credits["durationSeconds"], 180)
        self.assertEqual(credits["background"], "light")
        self.assertFalse(credits["skippable"])

    def test_playback_progress_is_stable_and_completes_at_duration(self) -> None:
        playback = build_native_credits_playback(
            {"durationSeconds": 10, "lines": ["A"]},
            started_at_ms=2_000,
        )

        self.assertEqual(get_native_credits_progress(playback, 1_000), 0.0)
        self.assertAlmostEqual(get_native_credits_progress(playback, 7_000), 0.5)
        self.assertFalse(is_native_credits_complete(playback, 11_999))
        self.assertTrue(can_advance_native_credits(playback, 2_000))
        self.assertTrue(is_native_credits_complete(playback, 12_000))
        self.assertEqual(get_native_credits_progress(playback, 50_000), 1.0)

        playback["skippable"] = False
        self.assertFalse(can_advance_native_credits(playback, 11_999))
        self.assertTrue(can_advance_native_credits(playback, 12_000))

    def test_layout_scrolls_full_content_and_static_mode_paginates(self) -> None:
        playback = build_native_credits_playback(
            {"durationSeconds": 20, "lines": [f"Line {index}" for index in range(18)]},
            started_at_ms=1_000,
        )
        scroll_start = build_native_credits_layout(1280, 720, playback, 1_000)
        scroll_end = build_native_credits_layout(1280, 720, playback, 21_000)
        static_middle = build_native_credits_layout(1280, 720, playback, 11_000, static_mode=True)

        self.assertEqual(scroll_start["mode"], "scroll")
        self.assertGreater(scroll_start["contentTop"], 720)
        self.assertLess(scroll_end["contentTop"], 0)
        self.assertEqual(static_middle["mode"], "pages")
        self.assertGreater(static_middle["pageCount"], 1)
        self.assertGreater(static_middle["pageIndex"], 0)
        self.assertLessEqual(len(static_middle["visibleLines"]), 10)


if __name__ == "__main__":
    unittest.main()
