from __future__ import annotations

import unittest

from native_runtime.runtime_player import NativeRuntimePlayer
from native_runtime.runtime_player_settings import sanitize_runtime_player_settings
from native_runtime.runtime_storage import sanitize_text_history_entries
from native_runtime.runtime_voice_mixer import (
    NARRATOR_VOICE_PROFILE_ID,
    collect_voice_mixer_entries,
    get_voice_mix_profile,
    get_voice_mix_volume_ratio,
    get_voice_mixer_summary,
    get_voice_profile_id_from_block,
    sanitize_voice_mix_profiles,
    update_voice_mix_profile,
)


class NativeRuntimeVoiceMixerTests(unittest.TestCase):
    def test_profiles_and_settings_are_safely_sanitized(self) -> None:
        profiles = sanitize_voice_mix_profiles(
            {
                "char_a": {"volume": 140, "muted": False},
                "char_b": "35",
                "constructor": {"volume": 0, "muted": True},
                "bad\x01id": {"volume": 10},
            }
        )
        settings = sanitize_runtime_player_settings({"voiceMix": profiles})
        adjusted = update_voice_mix_profile(profiles, "char_a", volume=62, muted=True)
        restored = update_voice_mix_profile(adjusted, "char_a", volume=100, muted=False)

        self.assertEqual(
            profiles,
            {
                "char_a": {"volume": 100, "muted": False},
                "char_b": {"volume": 35, "muted": False},
            },
        )
        self.assertEqual(settings["voiceMix"], profiles)
        self.assertEqual(get_voice_mix_profile(adjusted, "char_a"), {"volume": 62, "muted": True})
        self.assertEqual(get_voice_mix_volume_ratio(adjusted, "char_a"), 0)
        self.assertNotIn("char_a", restored)

    def test_entries_include_voiced_characters_and_narration(self) -> None:
        chapters = [
            {
                "scenes": [
                    {
                        "id": "scene_a",
                        "blocks": [
                            {"type": "dialogue", "speakerId": "char_a", "voiceAssetId": "voice_1"},
                            {"type": "dialogue", "speakerId": "char_a", "voiceAssetId": "voice_2"},
                            {"type": "narration", "voiceAssetId": "voice_n"},
                        ],
                    },
                    {
                        "id": "scene_b",
                        "blocks": [
                            {"type": "dialogue", "speakerId": "char_a", "voiceAssetId": "voice_3"},
                            {"type": "dialogue", "speakerId": "char_b", "text": "no voice"},
                        ],
                    },
                ]
            }
        ]
        entries = collect_voice_mixer_entries(
            chapters,
            {"char_a": {"displayName": "Yuina"}},
            get_character_name=lambda _character_id, character: str(character.get("displayName") or ""),
        )
        summary = get_voice_mixer_summary(entries, {"char_a": {"volume": 70, "muted": False}})

        self.assertEqual(entries[0], {"id": "char_a", "label": "Yuina", "lineCount": 3, "sceneCount": 2})
        self.assertEqual(entries[1]["id"], NARRATOR_VOICE_PROFILE_ID)
        self.assertEqual(get_voice_profile_id_from_block({"type": "narration"}), NARRATOR_VOICE_PROFILE_ID)
        self.assertEqual(summary, {"characterCount": 2, "customizedCount": 1, "mutedCount": 0})

    def test_native_player_volume_uses_global_character_and_line_levels(self) -> None:
        player = NativeRuntimePlayer.__new__(NativeRuntimePlayer)
        player.runtime_settings = {
            "masterVolume": 80,
            "voiceVolume": 50,
            "voiceMix": {"char_a": {"volume": 60, "muted": False}},
        }
        player.current_voice_volume_percent = 50
        player.current_voice_profile_id = "char_a"

        self.assertAlmostEqual(player.get_effective_voice_volume(), 0.12)
        player.runtime_settings["voiceMix"]["char_a"]["muted"] = True
        self.assertEqual(player.get_effective_voice_volume(), 0)

    def test_saved_history_preserves_line_volume_and_voice_profile(self) -> None:
        history = sanitize_text_history_entries(
            [
                {
                    "key": "line_1",
                    "text": "Hello",
                    "voiceAssetId": "voice_1",
                    "voiceVolume": 72,
                    "voiceProfileId": "char_a",
                }
            ]
        )

        self.assertEqual(history[0]["voiceVolume"], 72)
        self.assertEqual(history[0]["voiceProfileId"], "char_a")


if __name__ == "__main__":
    unittest.main()
