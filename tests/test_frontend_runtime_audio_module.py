from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_audio.js"


class FrontendRuntimeAudioModuleTests(unittest.TestCase):
    def test_runtime_audio_helpers_normalize_volume_fades_and_cleanup(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const disposed = {{ paused: false, src: "voice.ogg", pause() {{ this.paused = true; }} }};
            tools.disposeAudio(disposed, {{ cancelAnimationFrame() {{}} }});

            const stoppedA = {{ paused: false, src: "a.wav", pause() {{ this.paused = true; }} }};
            const stoppedB = {{ paused: false, src: "b.wav", pause() {{ this.paused = true; }} }};
            const tracked = new Set([stoppedA, stoppedB]);
            tools.stopTrackedAudios(tracked, {{ cancelAnimationFrame() {{}} }});

            const instantFade = {{ volume: 0.2 }};
            let instantComplete = false;
            tools.fadeAudioVolume(instantFade, {{
              from: 0.2,
              to: 0.8,
              durationMs: 0,
              onComplete() {{ instantComplete = true; }},
            }});

            const smoothFade = {{ volume: 0 }};
            let smoothComplete = false;
            const frameTimes = [100, 350, 600];
            const animationApi = {{
              performance: {{ now: () => 100 }},
              requestAnimationFrame(callback) {{
                callback(frameTimes.shift() ?? 600);
                return 7;
              }},
              cancelAnimationFrame() {{}},
            }};
            tools.fadeAudioVolume(smoothFade, {{
              from: 0,
              to: 1,
              durationMs: 500,
              onComplete() {{ smoothComplete = true; }},
              animationApi,
            }});

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              musicVolume: tools.getRuntimeMusicTargetVolume(
                {{ bgmVolume: 50 }},
                {{ visualState: {{ musicVolume: 60 }} }}
              ),
              musicBlockFallbackVolume: tools.getRuntimeMusicTargetVolume(
                {{ bgmVolume: 50 }},
                {{ block: {{ volume: 40 }} }}
              ),
              sfxVolume: tools.getRuntimeSfxTargetVolume({{ sfxVolume: 80 }}, 25),
              voiceVolume: tools.getRuntimeVoiceTargetVolume(
                {{ voiceVolume: 90 }},
                {{ block: {{ voiceVolume: 50 }} }}
              ),
              safeFade: tools.getSafeAudioFadeMs("900.2"),
              cappedFade: tools.getSafeAudioFadeMs(999999),
              badFade: tools.getSafeAudioFadeMs("bad", 1200),
              instantVolume: instantFade.volume,
              instantComplete,
              smoothVolume: smoothFade.volume,
              smoothComplete,
              disposed,
              stopped: [stoppedA, stoppedB],
              trackedSize: tracked.size,
            }}));
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("getRuntimeMusicTargetVolume", payload["keys"])
        self.assertIn("getRuntimeSfxTargetVolume", payload["keys"])
        self.assertIn("getRuntimeVoiceTargetVolume", payload["keys"])
        self.assertIn("fadeAudioVolume", payload["keys"])
        self.assertAlmostEqual(payload["musicVolume"], 0.3)
        self.assertAlmostEqual(payload["musicBlockFallbackVolume"], 0.2)
        self.assertAlmostEqual(payload["sfxVolume"], 0.2)
        self.assertAlmostEqual(payload["voiceVolume"], 0.45)
        self.assertEqual(payload["safeFade"], 900)
        self.assertEqual(payload["cappedFade"], 30000)
        self.assertEqual(payload["badFade"], 1200)
        self.assertAlmostEqual(payload["instantVolume"], 0.8)
        self.assertTrue(payload["instantComplete"])
        self.assertAlmostEqual(payload["smoothVolume"], 1)
        self.assertTrue(payload["smoothComplete"])
        self.assertEqual(payload["disposed"]["src"], "")
        self.assertTrue(payload["disposed"]["paused"])
        self.assertEqual(payload["trackedSize"], 0)
        self.assertTrue(all(item["paused"] and item["src"] == "" for item in payload["stopped"]))


if __name__ == "__main__":
    unittest.main()
