from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_music_transport.js"


class FrontendRuntimeMusicTransportModuleTests(unittest.TestCase):
    def test_transport_normalization_keys_and_audio_loop_controller(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            class FakeAudio {{
              constructor() {{
                this.currentTime = 0;
                this.duration = 30;
                this.readyState = 1;
                this.loop = false;
                this.ended = false;
                this.paused = false;
                this.playCount = 0;
                this.listeners = new Map();
              }}
              addEventListener(name, callback) {{ this.listeners.set(name, callback); }}
              removeEventListener(name) {{ this.listeners.delete(name); }}
              play() {{ this.playCount += 1; return Promise.resolve(); }}
              emit(name) {{ this.listeners.get(name)?.(); }}
            }}

            const legacy = tools.sanitizeMusicTransport({{}});
            const intro = tools.sanitizeMusicTransport({{
              loop: true,
              startTimeSeconds: 2,
              loopStartSeconds: 8,
              loopEndSeconds: 15,
            }});
            const invalidEnd = tools.sanitizeMusicTransport({{ loopStartSeconds: 9, loopEndSeconds: 4 }});
            const customAudio = new FakeAudio();
            const cleanupCustom = tools.bindMusicTransportToAudio(customAudio, intro);
            customAudio.currentTime = 15;
            customAudio.emit("timeupdate");
            const customResult = {{ currentTime: customAudio.currentTime, loop: customAudio.loop, playCount: customAudio.playCount }};
            cleanupCustom();

            const onceAudio = new FakeAudio();
            let stopped = 0;
            tools.bindMusicTransportToAudio(onceAudio, {{ loop: false }}, {{ onStopped() {{ stopped += 1; }} }});
            onceAudio.emit("ended");

            const pausedAudio = new FakeAudio();
            pausedAudio.paused = true;
            const keptPaused = tools.keepExistingMusicPlaybackAlive(pausedAudio);
            const endedAudio = new FakeAudio();
            endedAudio.ended = true;
            const keptEnded = tools.keepExistingMusicPlaybackAlive(endedAudio);

            process.stdout.write(JSON.stringify({{
              legacy,
              intro,
              invalidEnd,
              customResult,
              once: {{ stopped, playCount: onceAudio.playCount, loop: onceAudio.loop }},
              reuse: {{ keptPaused, pausedPlayCount: pausedAudio.playCount, keptEnded, endedPlayCount: endedAudio.playCount }},
              continueKeysEqual:
                tools.buildMusicPlaybackKey("bgm", {{ restartMode: "continue" }}, "a") ===
                tools.buildMusicPlaybackKey("bgm", {{ restartMode: "continue" }}, "b"),
              restartKeysEqual:
                tools.buildMusicPlaybackKey("bgm", {{ restartMode: "restart" }}, "a") ===
                tools.buildMusicPlaybackKey("bgm", {{ restartMode: "restart" }}, "b"),
              summary: tools.getMusicTransportSummary(intro),
              diagnostic: tools.getMusicTransportDiagnostics({{ loopStartSeconds: 9, loopEndSeconds: 4 }}),
              globalAttached: Boolean(globalThis.CanvasiaRuntimeMusicTransport),
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
        self.assertEqual(payload["legacy"]["loop"], True)
        self.assertEqual(payload["legacy"]["restartMode"], "continue")
        self.assertEqual(payload["intro"]["loopStartSeconds"], 8)
        self.assertEqual(payload["invalidEnd"]["loopEndSeconds"], 0)
        self.assertEqual(payload["customResult"], {"currentTime": 8, "loop": False, "playCount": 1})
        self.assertEqual(payload["once"], {"stopped": 1, "playCount": 0, "loop": False})
        self.assertEqual(
            payload["reuse"],
            {"keptPaused": True, "pausedPlayCount": 1, "keptEnded": False, "endedPlayCount": 0},
        )
        self.assertTrue(payload["continueKeysEqual"])
        self.assertFalse(payload["restartKeysEqual"])
        self.assertIn("循环 8 秒", payload["summary"])
        self.assertEqual(payload["diagnostic"]["level"], "warning")
        self.assertTrue(payload["globalAttached"])


if __name__ == "__main__":
    unittest.main()
