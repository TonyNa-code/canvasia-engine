from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_voice_reactive_motion.js"


class FrontendRuntimeVoiceReactiveMotionModuleTests(unittest.TestCase):
    def test_config_level_and_presentation_are_safe(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};
            const config = tools.getVoiceReactiveMotionConfig({{
              voiceReactiveMotionMode: "broken",
              voiceReactiveMotionIntensity: 999,
              voiceReactiveMotionSensitivity: -20,
            }});
            const attack = tools.normalizeVoiceReactiveLevel(0.5, 62, 0);
            const release = tools.normalizeVoiceReactiveLevel(0, 62, attack);
            const active = tools.buildVoiceReactiveMotionPresentation({{
              characterId: "hero",
              activeCharacterId: "hero",
              voiceActive: true,
              voiceLevel: 0.75,
              gameUiConfig: {{ voiceReactiveMotionMode: "cinematic", voiceReactiveMotionIntensity: 80 }},
            }});
            const staticPose = tools.buildVoiceReactiveMotionPose({{
              characterId: "hero",
              activeCharacterId: "hero",
              voiceActive: true,
              voiceLevel: 0.75,
              visualComfortMode: "static",
            }});
            process.stdout.write(JSON.stringify({{ config, attack, release, active, staticPose }}));
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
            payload["config"],
            {
                "voiceReactiveMotionMode": "soft",
                "voiceReactiveMotionIntensity": 100,
                "voiceReactiveMotionSensitivity": 0,
            },
        )
        self.assertGreater(payload["attack"], 0)
        self.assertLess(payload["release"], payload["attack"])
        self.assertTrue(payload["active"]["active"])
        self.assertIn("is-voice-reactive", payload["active"]["classNames"])
        self.assertIn("--voice-reactive-mouth", payload["active"]["style"])
        self.assertFalse(payload["staticPose"]["active"])

    def test_controller_disconnects_audio_graph_and_sleeps_while_paused(self) -> None:
        script = textwrap.dedent(
            f"""
            import {{ createVoiceReactiveMotionController }} from {json.dumps(MODULE_PATH.as_uri())};

            let scheduled = null;
            let cancelled = 0;
            let sourceConnects = 0;
            let sourceDisconnects = 0;
            let analyserConnects = 0;
            let analyserDisconnects = 0;
            const listeners = new Map();
            const audio = {{
              paused: true,
              ended: false,
              currentTime: 0,
              addEventListener(type, listener) {{ listeners.set(type, listener); }},
              removeEventListener(type, listener) {{
                if (listeners.get(type) === listener) listeners.delete(type);
              }},
            }};
            const sourceNode = {{
              connect() {{ sourceConnects += 1; }},
              disconnect() {{ sourceDisconnects += 1; }},
            }};
            const analyser = {{
              fftSize: 0,
              smoothingTimeConstant: 0,
              connect() {{ analyserConnects += 1; }},
              disconnect() {{ analyserDisconnects += 1; }},
              getByteTimeDomainData(data) {{ data.fill(140); }},
            }};
            const audioContext = {{
              destination: {{}},
              createMediaElementSource() {{ return sourceNode; }},
              createAnalyser() {{ return analyser; }},
              resume() {{ return Promise.resolve(); }},
            }};
            const animationApi = {{
              requestAnimationFrame(callback) {{ scheduled = callback; return 1; }},
              cancelAnimationFrame() {{ cancelled += 1; scheduled = null; }},
            }};
            const root = {{ querySelectorAll() {{ return []; }} }};
            const controller = createVoiceReactiveMotionController({{
              audioContextFactory: () => audioContext,
              animationApi,
              resolveRoot: () => root,
            }});

            controller.start({{ audio, characterId: "hero" }});
            const scheduledBeforePlay = Boolean(scheduled);
            const pausedFrame = scheduled;
            scheduled = null;
            pausedFrame(0);
            const sleepingWhilePaused = scheduled === null;
            audio.paused = false;
            listeners.get("playing")?.();
            const scheduledAfterPlay = Boolean(scheduled);
            const playingFrame = scheduled;
            scheduled = null;
            playingFrame(16);
            const activeLoopScheduled = Boolean(scheduled);
            audio.paused = true;
            listeners.get("pause")?.();
            const sleepingAfterPauseEvent = scheduled === null;
            controller.stop();
            audio.paused = false;
            controller.start({{ audio, characterId: "hero" }});
            audio.ended = true;
            listeners.get("ended")?.();

            process.stdout.write(JSON.stringify({{
              scheduledBeforePlay,
              sleepingWhilePaused,
              scheduledAfterPlay,
              activeLoopScheduled,
              sleepingAfterPauseEvent,
              sourceConnects,
              sourceDisconnects,
              analyserConnects,
              analyserDisconnects,
              listenerCount: listeners.size,
              cancelled,
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

        self.assertTrue(payload["scheduledBeforePlay"])
        self.assertTrue(payload["sleepingWhilePaused"])
        self.assertTrue(payload["scheduledAfterPlay"])
        self.assertTrue(payload["activeLoopScheduled"])
        self.assertTrue(payload["sleepingAfterPauseEvent"])
        self.assertEqual(payload["sourceConnects"], 2)
        self.assertEqual(payload["sourceDisconnects"], 2)
        self.assertEqual(payload["analyserConnects"], 2)
        self.assertEqual(payload["analyserDisconnects"], 2)
        self.assertEqual(payload["listenerCount"], 0)


if __name__ == "__main__":
    unittest.main()
