from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_preload.js"


class FrontendRuntimePreloadModuleTests(unittest.TestCase):
    def test_runtime_preload_prioritizes_critical_assets_and_reports_progress(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const events = [];
            class FakeImage {{
              set src(value) {{
                this._src = value;
                queueMicrotask(() => this.onload?.());
              }}
              get src() {{
                return this._src;
              }}
            }}

            class FakeAudio {{
              set src(value) {{
                this._src = value;
              }}
              get src() {{
                return this._src;
              }}
              load() {{
                queueMicrotask(() => this.onloadedmetadata?.());
              }}
            }}

            const fakeDocument = {{
              createElement(tag) {{
                return {{
                  tag,
                  removeAttribute() {{}},
                  load() {{
                    queueMicrotask(() => this.onloadedmetadata?.());
                  }},
                }};
              }},
            }};

            const manifest = {{
              formatVersion: 1,
              entries: [
                {{ assetId: "bg_intro", type: "background", url: "assets/background/bg_intro.png", phase: "critical", priority: 100 }},
                {{ assetId: "bgm_intro", type: "bgm", url: "assets/bgm/intro.wav", phase: "early", priority: 72, sizeBytes: 4096 }},
                {{ assetId: "op_video", type: "video", url: "assets/video/op.mp4", phase: "deferred", priority: 30, sizeBytes: 8192 }},
              ],
            }};

            const summary = tools.getRuntimePreloadSummary(manifest);
            const controller = tools.startRuntimePreload(manifest, {{
              ImageCtor: FakeImage,
              AudioCtor: FakeAudio,
              documentRef: fakeDocument,
              requestIdleCallback(callback) {{ callback(); }},
              timeoutMs: 500,
              onProgress(status) {{ events.push(status); }},
            }});

            await new Promise((resolve) => setTimeout(resolve, 0));
            await new Promise((resolve) => setTimeout(resolve, 0));

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              summary,
              status: controller.getStatus(),
              eventCount: events.length,
              normalized: tools.normalizeRuntimePreloadManifest(manifest).entries.map((entry) => entry.assetId),
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
        self.assertIn("startRuntimePreload", payload["keys"])
        self.assertIn("getRuntimePreloadSummary", payload["keys"])
        self.assertEqual(payload["summary"]["totalCount"], 3)
        self.assertEqual(payload["summary"]["criticalCount"], 1)
        self.assertEqual(payload["summary"]["imageCount"], 1)
        self.assertEqual(payload["summary"]["audioCount"], 1)
        self.assertEqual(payload["summary"]["videoCount"], 1)
        self.assertEqual(payload["summary"]["totalSizeBytes"], 12288)
        self.assertEqual(payload["summary"]["earlySizeBytes"], 4096)
        self.assertEqual(payload["summary"]["videoSizeBytes"], 8192)
        self.assertEqual(payload["normalized"][0], "bg_intro")
        self.assertEqual(payload["status"]["loadedCount"], 3)
        self.assertEqual(payload["status"]["failedCount"], 0)
        self.assertTrue(payload["status"]["finished"])
        self.assertGreaterEqual(payload["eventCount"], 3)

    def test_runtime_preload_limits_concurrency_and_delays_deferred_assets(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const pending = [];
            const idleCallbacks = [];
            const started = [];
            const events = [];
            let browserActive = 0;
            let maxBrowserActive = 0;

            function tick() {{
              return new Promise((resolve) => setTimeout(resolve, 0));
            }}

            class SlowImage {{
              set src(value) {{
                this._src = value;
                started.push(value);
                browserActive += 1;
                maxBrowserActive = Math.max(maxBrowserActive, browserActive);
                pending.push(() => {{
                  browserActive -= 1;
                  this.onload?.();
                }});
              }}
              get src() {{
                return this._src;
              }}
            }}

            const manifest = {{
              formatVersion: 1,
              entries: [
                {{ assetId: "critical_a", type: "background", url: "assets/background/a.png", phase: "critical", priority: 100 }},
                {{ assetId: "critical_b", type: "background", url: "assets/background/b.png", phase: "critical", priority: 99 }},
                {{ assetId: "critical_c", type: "background", url: "assets/background/c.png", phase: "critical", priority: 98 }},
                {{ assetId: "critical_d", type: "background", url: "assets/background/d.png", phase: "critical", priority: 97 }},
                {{ assetId: "early_a", type: "background", url: "assets/background/early.png", phase: "early", priority: 72 }},
              ],
            }};

            const controller = tools.startRuntimePreload(manifest, {{
              ImageCtor: SlowImage,
              maxConcurrent: 2,
              requestIdleCallback(callback) {{ idleCallbacks.push(callback); }},
              timeoutMs: 500,
              onProgress(status) {{ events.push(status); }},
            }});

            await tick();
            const afterStart = controller.getStatus();
            const firstWave = started.map((value) => value.split("/").pop());

            while (pending.length) {{
              const finish = pending.shift();
              finish();
              await tick();
              if (controller.getStatus().loadedCount >= 4) {{
                break;
              }}
            }}
            await tick();
            const beforeIdle = controller.getStatus();
            const beforeIdleStarted = started.map((value) => value.split("/").pop());

            idleCallbacks.shift()?.();
            await tick();
            const afterIdleStarted = started.map((value) => value.split("/").pop());
            while (pending.length) {{
              const finish = pending.shift();
              finish();
              await tick();
            }}
            await tick();

            process.stdout.write(JSON.stringify({{
              afterStart,
              beforeIdle,
              finalStatus: controller.getStatus(),
              firstWave,
              beforeIdleStarted,
              afterIdleStarted,
              maxBrowserActive,
              eventCount: events.length,
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
        self.assertEqual(payload["afterStart"]["activeCount"], 2)
        self.assertEqual(payload["afterStart"]["maxConcurrent"], 2)
        self.assertEqual(payload["firstWave"], ["a.png", "b.png"])
        self.assertEqual(payload["beforeIdle"]["loadedCount"], 4)
        self.assertFalse(payload["beforeIdle"]["finished"])
        self.assertNotIn("early.png", payload["beforeIdleStarted"])
        self.assertIn("early.png", payload["afterIdleStarted"])
        self.assertLessEqual(payload["maxBrowserActive"], 2)
        self.assertEqual(payload["finalStatus"]["loadedCount"], 5)
        self.assertTrue(payload["finalStatus"]["finished"])
        self.assertGreaterEqual(payload["eventCount"], 5)


if __name__ == "__main__":
    unittest.main()
