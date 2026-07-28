from __future__ import annotations

import struct
import unittest

from native_runtime.runtime_voice_reactive_motion import (
    NativeVoiceReactiveMotionController,
    build_native_voice_reactive_motion_pose,
    build_pcm_voice_envelope,
    normalize_voice_reactive_level,
    sanitize_voice_reactive_motion_config,
)


class _FakeSound:
    def __init__(self, raw: bytes, length: float = 0.2) -> None:
        self._raw = raw
        self._length = length

    def get_raw(self) -> bytes:
        return self._raw

    def get_length(self) -> float:
        return self._length


class NativeRuntimeVoiceReactiveMotionTests(unittest.TestCase):
    def test_config_clamps_author_controls(self) -> None:
        config = sanitize_voice_reactive_motion_config(
            {
                "voiceReactiveMotionMode": "broken",
                "voiceReactiveMotionIntensity": 999,
                "voiceReactiveMotionSensitivity": -20,
            }
        )

        self.assertEqual(
            config,
            {
                "voiceReactiveMotionMode": "soft",
                "voiceReactiveMotionIntensity": 100,
                "voiceReactiveMotionSensitivity": 0,
            },
        )

    def test_pose_targets_only_the_active_speaker_and_respects_comfort(self) -> None:
        active = build_native_voice_reactive_motion_pose(
            character_id="hero",
            active_character_id="hero",
            voice_active=True,
            voice_level=0.8,
            game_ui_config={"voiceReactiveMotionMode": "cinematic", "voiceReactiveMotionIntensity": 80},
        )
        inactive = build_native_voice_reactive_motion_pose(
            character_id="heroine",
            active_character_id="hero",
            voice_active=True,
            voice_level=0.8,
        )
        static = build_native_voice_reactive_motion_pose(
            character_id="hero",
            active_character_id="hero",
            voice_active=True,
            voice_level=0.8,
            visual_comfort_mode="static",
        )

        self.assertTrue(active["active"])
        self.assertGreater(active["mouthOpen"], 0)
        self.assertGreater(active["scaleMultiplier"], 1)
        self.assertLess(active["offsetYPercent"], 0)
        self.assertFalse(inactive["active"])
        self.assertFalse(static["active"])
        self.assertEqual(static["mouthOpen"], 0)

    def test_pcm_envelope_distinguishes_silence_from_voice_energy(self) -> None:
        silence = struct.pack("<" + "h" * 160, *([0] * 160))
        voiced = struct.pack("<" + "h" * 160, *([18000, -18000] * 80))

        silent_envelope = build_pcm_voice_envelope(silence, (1000, -16, 1))
        voiced_envelope = build_pcm_voice_envelope(voiced, (1000, -16, 1))

        self.assertTrue(silent_envelope)
        self.assertTrue(voiced_envelope)
        self.assertEqual(max(silent_envelope), 0)
        self.assertGreater(min(voiced_envelope), 0.5)

    def test_controller_uses_pcm_timing_and_releases_smoothly(self) -> None:
        raw = struct.pack("<" + "h" * 200, *([16000, -16000] * 100))
        controller = NativeVoiceReactiveMotionController()
        controller.start(_FakeSound(raw), "hero", 1000, (1000, -16, 1))

        active_level = controller.get_level(1040, True, 62)
        release_level = controller.get_level(1080, False, 62)

        self.assertEqual(controller.character_id, "hero")
        self.assertGreater(active_level, 0)
        self.assertGreater(release_level, 0)
        self.assertLess(release_level, active_level)
        self.assertGreater(normalize_voice_reactive_level(0.5, 62, 0), 0)


if __name__ == "__main__":
    unittest.main()
