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
                {{ assetId: "bgm_intro", type: "bgm", url: "assets/bgm/intro.wav", phase: "early", priority: 72 }},
                {{ assetId: "op_video", type: "video", url: "assets/video/op.mp4", phase: "deferred", priority: 30 }},
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
        self.assertEqual(payload["normalized"][0], "bg_intro")
        self.assertEqual(payload["status"]["loadedCount"], 3)
        self.assertEqual(payload["status"]["failedCount"], 0)
        self.assertTrue(payload["status"]["finished"])
        self.assertGreaterEqual(payload["eventCount"], 3)


if __name__ == "__main__":
    unittest.main()
