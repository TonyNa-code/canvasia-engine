from __future__ import annotations

import unittest

from native_runtime.runtime_reading_profiles import (
    READING_PROFILE_IDS,
    apply_reading_profile,
    detect_reading_profile,
    get_reading_profile_summary,
    get_safe_dialog_box_opacity_percent,
    get_safe_reading_text_scale_percent,
)


class NativeRuntimeReadingProfilesTests(unittest.TestCase):
    def test_profiles_apply_detect_and_preserve_unrelated_settings(self) -> None:
        large = apply_reading_profile({"language": "ja-JP", "bgmVolume": 64}, "large")

        self.assertEqual(READING_PROFILE_IDS, ("standard", "comfortable", "large", "calm"))
        self.assertEqual(large["language"], "ja-JP")
        self.assertEqual(large["bgmVolume"], 64)
        self.assertEqual(large["textSpeed"], "slow")
        self.assertEqual(large["textScalePercent"], 125)
        self.assertEqual(large["visualComfort"], "gentle")
        self.assertEqual(detect_reading_profile(large), "large")

        custom = {**large, "dialogBoxOpacityPercent": 60}
        self.assertEqual(detect_reading_profile(custom), "custom")
        self.assertEqual(get_reading_profile_summary(custom)["label"], "自定义组合")
        self.assertEqual(get_safe_reading_text_scale_percent(999), 125)
        self.assertEqual(get_safe_dialog_box_opacity_percent(-10), 0)


if __name__ == "__main__":
    unittest.main()
