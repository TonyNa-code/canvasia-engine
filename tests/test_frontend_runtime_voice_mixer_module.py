from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_voice_mixer.js"
SETTINGS_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_settings.js"


def run_node_module(script_body: str) -> dict:
    script = textwrap.dedent(
        f"""
        import * as tools from {json.dumps(MODULE_PATH.as_uri())};
        import * as settingsTools from {json.dumps(SETTINGS_MODULE_PATH.as_uri())};
        {script_body}
        """
    )
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


class FrontendRuntimeVoiceMixerModuleTests(unittest.TestCase):
    def test_profiles_are_sanitized_updated_and_applied_as_volume_ratios(self) -> None:
        payload = run_node_module(
            """
            const polluted = { char_a: { volume: 125, muted: false }, char_b: 35 };
            Object.defineProperty(polluted, "__proto__", { value: { volume: 1 }, enumerable: true });
            polluted[`bad${String.fromCharCode(1)}id`] = { volume: 20 };
            const sanitized = tools.sanitizeVoiceMixProfiles(polluted);
            const adjusted = tools.updateVoiceMixProfile(sanitized, "char_a", { volume: 62, muted: true });
            const restored = tools.updateVoiceMixProfile(adjusted, "char_a", { volume: 100, muted: false });
            const playback = settingsTools.sanitizePlaybackSettings({
              voiceMix: {
                char_a: { volume: 55, muted: false },
                constructor: { volume: 0, muted: true },
              },
            });
            process.stdout.write(JSON.stringify({
              sanitized,
              adjusted,
              restored,
              mutedRatio: tools.getVoiceMixVolumeRatio(adjusted, "char_a"),
              numericRatio: tools.getVoiceMixVolumeRatio(sanitized, "char_b"),
              defaultRatio: tools.getVoiceMixVolumeRatio(sanitized, "missing"),
              playbackVoiceMix: playback.voiceMix,
              safeNarrator: tools.getVoiceProfileIdFromBlock({ type: "narration" }),
              safeSpeaker: tools.getVoiceProfileIdFromSnapshot({ block: { type: "dialogue", speakerId: "char_a" } }),
            }));
            """
        )

        self.assertEqual(payload["sanitized"], {"char_a": {"volume": 100, "muted": False}, "char_b": {"volume": 35, "muted": False}})
        self.assertEqual(payload["adjusted"]["char_a"], {"volume": 62, "muted": True})
        self.assertNotIn("char_a", payload["restored"])
        self.assertEqual(payload["mutedRatio"], 0)
        self.assertAlmostEqual(payload["numericRatio"], 0.35)
        self.assertEqual(payload["defaultRatio"], 1)
        self.assertEqual(payload["playbackVoiceMix"], {"char_a": {"volume": 55, "muted": False}})
        self.assertEqual(payload["safeNarrator"], "__canvasia_narrator__")
        self.assertEqual(payload["safeSpeaker"], "char_a")

    def test_entries_and_markup_cover_characters_narration_and_safe_rendering(self) -> None:
        payload = run_node_module(
            """
            const escapeHtml = (value) => String(value ?? "")
              .replaceAll("&", "&amp;")
              .replaceAll("<", "&lt;")
              .replaceAll(">", "&gt;")
              .replaceAll('"', "&quot;");
            const entries = tools.collectVoiceMixerEntries({
              scenes: [
                { id: "scene_a", blocks: [
                  { type: "dialogue", speakerId: "char_a", voiceAssetId: "voice_1" },
                  { type: "dialogue", speakerId: "char_a", voiceAssetId: "voice_2" },
                  { type: "narration", voiceAssetId: "voice_n" },
                  { type: "dialogue", speakerId: "char_b", text: "no voice" },
                ] },
                { id: "scene_b", blocks: [
                  { type: "dialogue", speakerId: "char_a", voiceAssetId: "voice_3" },
                ] },
              ],
              charactersById: new Map([["char_a", { displayName: "<Yuina>" }]]),
              getCharacterName: (_id, character) => character?.displayName,
            });
            const profiles = { char_a: { volume: 64, muted: false }, __canvasia_narrator__: { volume: 100, muted: true } };
            process.stdout.write(JSON.stringify({
              entries,
              summary: tools.getVoiceMixerSummary(entries, profiles),
              markup: tools.renderVoiceMixerRows(entries, profiles, { escapeHtml }),
            }));
            """
        )

        self.assertEqual(payload["entries"][0], {"id": "char_a", "label": "<Yuina>", "lineCount": 3, "sceneCount": 2})
        self.assertEqual(payload["entries"][1]["id"], "__canvasia_narrator__")
        self.assertEqual(payload["summary"], {"characterCount": 2, "customizedCount": 2, "mutedCount": 1})
        self.assertIn("&lt;Yuina&gt;", payload["markup"])
        self.assertNotIn("<Yuina>", payload["markup"])
        self.assertIn("data-voice-mixer-volume", payload["markup"])
        self.assertIn("已静音", payload["markup"])


if __name__ == "__main__":
    unittest.main()
