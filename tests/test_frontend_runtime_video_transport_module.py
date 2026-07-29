from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_video_transport.js"


class FrontendRuntimeVideoTransportModuleTests(unittest.TestCase):
    def test_transport_normalization_resume_and_video_binding(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            class FakeVideo {{
              constructor() {{
                this.currentTime = 0;
                this.duration = 30;
                this.readyState = 1;
                this.loop = true;
                this.volume = 1;
                this.playCount = 0;
                this.listeners = new Map();
              }}
              addEventListener(name, callback) {{ this.listeners.set(name, callback); }}
              removeEventListener(name) {{ this.listeners.delete(name); }}
              play() {{ this.playCount += 1; return Promise.resolve(); }}
              emit(name) {{ this.listeners.get(name)?.(); }}
            }}

            const legacy = tools.sanitizeVideoTransport({{}});
            const invalidEnd = tools.sanitizeVideoTransport({{
              startTimeSeconds: 8,
              endTimeSeconds: 4,
              fit: "broken",
              volume: 400,
            }});
            const safeLoop = tools.sanitizeVideoTransport({{ loop: true, skippable: false }});
            const resumed = tools.getVideoInitialPosition({{
              resumeMode: "resume",
              startTimeSeconds: 2,
              endTimeSeconds: 9,
            }}, 6.25);
            const wrappedResume = tools.getVideoInitialPosition({{
              resumeMode: "resume",
              startTimeSeconds: 2,
              endTimeSeconds: 9,
            }}, 10);

            const loopVideo = new FakeVideo();
            let loopCount = 0;
            const cleanupLoop = tools.bindVideoTransportToVideo(loopVideo, {{
              loop: true,
              startTimeSeconds: 2,
              endTimeSeconds: 5,
              volume: 40,
            }}, {{ onLoop() {{ loopCount += 1; }} }});
            loopVideo.currentTime = 5;
            loopVideo.emit("timeupdate");
            const loopResult = {{
              currentTime: loopVideo.currentTime,
              nativeLoop: loopVideo.loop,
              volume: loopVideo.volume,
              playCount: loopVideo.playCount,
              loopCount,
            }};
            cleanupLoop();

            const onceVideo = new FakeVideo();
            let finishReason = "";
            tools.bindVideoTransportToVideo(onceVideo, {{ loop: false }}, {{
              onFinished(reason) {{ finishReason = reason; }},
            }});
            onceVideo.emit("ended");
            onceVideo.emit("ended");

            process.stdout.write(JSON.stringify({{
              legacy,
              invalidEnd,
              safeLoop,
              resumed,
              wrappedResume,
              loopResult,
              finishReason,
              summary: tools.getVideoTransportSummary({{ autoplay: false, loop: true, resumeMode: "resume" }}),
              diagnostic: tools.getVideoTransportDiagnostics({{ loop: true, skippable: false }}),
              globalAttached: Boolean(globalThis.CanvasiaRuntimeVideoTransport),
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
                "autoplay": True,
                "loop": False,
                "resumeMode": "restart",
                "startTimeSeconds": 0,
                "endTimeSeconds": 0,
                "fit": "contain",
                "volume": 100,
                "skippable": True,
            },
        )
        self.assertEqual(payload["invalidEnd"]["endTimeSeconds"], 0)
        self.assertEqual(payload["invalidEnd"]["fit"], "contain")
        self.assertEqual(payload["invalidEnd"]["volume"], 100)
        self.assertTrue(payload["safeLoop"]["skippable"])
        self.assertEqual(payload["resumed"], 6.25)
        self.assertEqual(payload["wrappedResume"], 2)
        self.assertEqual(
            payload["loopResult"],
            {"currentTime": 2, "nativeLoop": False, "volume": 0.4, "playCount": 1, "loopCount": 1},
        )
        self.assertEqual(payload["finishReason"], "ended")
        self.assertIn("等待玩家手动播放", payload["summary"])
        self.assertEqual(payload["diagnostic"]["code"], "loop_requires_exit")
        self.assertTrue(payload["globalAttached"])


if __name__ == "__main__":
    unittest.main()
