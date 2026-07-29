from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_sfx_transport.js"


class FrontendRuntimeSfxTransportModuleTests(unittest.TestCase):
    def test_channels_overlap_persist_replace_stop_and_retry_safely(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const audios = [];
            const fadeCalls = [];
            let missingReady = false;
            let masterVolume = 0.5;

            class FakeAudio {{
              constructor(url) {{
                this.url = url;
                this.src = url;
                this.loop = false;
                this.volume = 1;
                this.paused = false;
                this.ended = false;
                this.playCount = 0;
                this.disposeCount = 0;
                this.listeners = new Map();
                audios.push(this);
              }}
              addEventListener(name, callback) {{ this.listeners.set(name, callback); }}
              play() {{ this.playCount += 1; this.paused = false; return Promise.resolve(); }}
              pause() {{ this.paused = true; this.disposeCount += 1; }}
              removeAttribute() {{}}
              load() {{}}
              emit(name) {{ this.listeners.get(name)?.(); }}
            }}

            const fadeAudio = (audio, detail) => {{
              fadeCalls.push({{ url: audio.url, durationMs: detail.durationMs, from: detail.from, to: detail.to }});
              audio.volume = detail.to;
              detail.onComplete?.();
            }};
            const controller = tools.createSfxTransportController({{
              AudioClass: FakeAudio,
              resolveAssetUrl(assetId) {{
                if (assetId === "missing" && !missingReady) return "";
                return `/assets/${{assetId}}.ogg`;
              }},
              getMasterVolume() {{ return masterVolume; }},
              fadeAudio,
            }});

            const legacy = tools.sanitizeSfxTransport({{}});
            const invalid = tools.sanitizeSfxTransport({{
              channelId: "broken",
              volume: 900,
              fadeInMs: -20,
              replaceFadeOutMs: 999999,
            }});
            const rainState = tools.applySfxBlockToChannelState({{}}, {{
              id: "rain-a",
              type: "sfx_play",
              assetId: "rain",
              channelId: "ambience",
              loop: true,
              restartMode: "continue",
              volume: 60,
              fadeInMs: 200,
              replaceFadeOutMs: 500,
            }});
            const unchangedByOneShot = tools.applySfxBlockToChannelState(rainState, {{
              type: "sfx_play",
              assetId: "click",
              loop: false,
            }});

            controller.sync({{
              blockType: "sfx_play",
              block: {{ type: "sfx_play", assetId: "click", channelId: "effect", volume: 100 }},
              visualState: {{ sfxChannels: {{}} }},
            }}, {{ stepKey: "step-1" }});
            controller.sync({{
              blockType: "sfx_play",
              block: {{ type: "sfx_play", assetId: "click", channelId: "effect", volume: 100 }},
              visualState: {{ sfxChannels: {{}} }},
            }}, {{ stepKey: "step-1" }});
            const afterDuplicate = controller.getDebugState();
            controller.triggerOneShot({{ type: "sfx_play", assetId: "click", channelId: "effect" }}, "step-2");
            const afterOverlap = controller.getDebugState();

            controller.sync({{ blockType: "dialogue", visualState: {{ sfxChannels: rainState }} }});
            const rainAudio = audios.at(-1);
            controller.syncPersistentChannels({{
              ambience: {{ ...rainState.ambience, cueId: "rain-b" }},
            }});
            const afterContinue = controller.getDebugState();

            const windState = tools.applySfxBlockToChannelState(rainState, {{
              id: "wind-a",
              type: "sfx_play",
              assetId: "wind",
              channelId: "ambience",
              loop: true,
              restartMode: "continue",
              volume: 40,
              replaceFadeOutMs: 700,
            }});
            controller.syncPersistentChannels(windState);
            const afterReplace = controller.getDebugState();

            masterVolume = 1;
            controller.updateVolumes();
            const afterVolume = controller.getDebugState();
            controller.stop("effect", 250);
            const afterEffectStop = controller.getDebugState();
            controller.stop("all", 300);
            const afterAllStop = controller.getDebugState();

            const firstMissing = controller.triggerOneShot({{ type: "sfx_play", assetId: "missing" }}, "retry-key");
            missingReady = true;
            const retriedMissing = controller.triggerOneShot({{ type: "sfx_play", assetId: "missing" }}, "retry-key");

            process.stdout.write(JSON.stringify({{
              legacy,
              invalid,
              rainState,
              unchangedByOneShot,
              stoppedState: tools.applySfxBlockToChannelState(rainState, {{ type: "sfx_stop", channelId: "ambience" }}),
              afterDuplicate,
              afterOverlap,
              afterContinue,
              afterReplace,
              afterVolume,
              afterEffectStop,
              afterAllStop,
              rainPlayCount: rainAudio.playCount,
              rainDisposeCount: rainAudio.disposeCount,
              fadeDurations: fadeCalls.map((item) => item.durationMs),
              firstMissing,
              retriedMissing,
              globalAttached: Boolean(globalThis.CanvasiaRuntimeSfxTransport),
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
        self.assertEqual(
            payload["legacy"],
            {
                "channelId": "effect",
                "loop": False,
                "restartMode": "restart",
                "volume": 100,
                "fadeInMs": 0,
                "replaceFadeOutMs": 0,
            },
        )
        self.assertEqual(payload["invalid"]["channelId"], "effect")
        self.assertEqual(payload["invalid"]["volume"], 100)
        self.assertEqual(payload["invalid"]["fadeInMs"], 0)
        self.assertEqual(payload["invalid"]["replaceFadeOutMs"], 60000)
        self.assertEqual(payload["rainState"], payload["unchangedByOneShot"])
        self.assertEqual(payload["stoppedState"], {})
        self.assertEqual(payload["afterDuplicate"]["oneShotCount"], 1)
        self.assertEqual(payload["afterOverlap"]["oneShotCount"], 2)
        self.assertEqual(payload["afterContinue"]["persistentChannels"]["ambience"]["assetId"], "rain")
        self.assertEqual(payload["rainPlayCount"], 1)
        self.assertEqual(payload["rainDisposeCount"], 1)
        self.assertEqual(payload["afterReplace"]["persistentChannels"]["ambience"]["assetId"], "wind")
        self.assertEqual(payload["afterVolume"]["persistentChannels"]["ambience"]["volume"], 0.4)
        self.assertEqual(payload["afterEffectStop"]["oneShotCount"], 0)
        self.assertIn("ambience", payload["afterEffectStop"]["persistentChannels"])
        self.assertEqual(payload["afterAllStop"]["persistentChannels"], {})
        self.assertIn(700, payload["fadeDurations"])
        self.assertIn(250, payload["fadeDurations"])
        self.assertIn(300, payload["fadeDurations"])
        self.assertFalse(payload["firstMissing"])
        self.assertTrue(payload["retriedMissing"])
        self.assertTrue(payload["globalAttached"])


if __name__ == "__main__":
    unittest.main()
