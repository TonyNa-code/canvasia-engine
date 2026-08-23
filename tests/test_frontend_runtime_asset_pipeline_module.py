from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_asset_pipeline.js"


class FrontendRuntimeAssetPipelineModuleTests(unittest.TestCase):
    def test_pipeline_owns_cache_lifecycle_and_avoids_same_step_prefetch_thrash(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            let nowMs = 100;
            const controllers = [];
            const manifestCalls = [];

            function startPreload(manifest, options) {{
              let status = {{
                totalCount: manifest.entries.length,
                loadedCount: 0,
                failedCount: 0,
                skippedCount: 0,
                pendingCount: manifest.entries.length,
                finished: false,
                loadedAssetIds: [],
                failedAssetIds: [],
                skippedAssetIds: [],
              }};
              const controller = {{
                stopped: false,
                manifest,
                options,
                stop() {{ this.stopped = true; }},
                getStatus() {{ return {{ ...status }}; }},
                finish(nextStatus) {{
                  status = {{ ...status, ...nextStatus, pendingCount: 0, finished: true }};
                  options.onProgress(status);
                }},
              }};
              controllers.push(controller);
              return controller;
            }}

            function buildPrefetchManifest(snapshot, context) {{
              manifestCalls.push({{
                blockId: snapshot.blockId,
                excluded: Array.from(context.excludeAssetIds).sort(),
              }});
              return {{
                formatVersion: 1,
                entries: [
                  {{ assetId: "route-a", type: "background", url: "route-a.png", phase: "early" }},
                  {{ assetId: "route-b", type: "background", url: "route-b.png", phase: "early" }},
                ],
              }};
            }}

            const events = [];
            const pipeline = tools.createRuntimeAssetPipeline({{
              preloadManifest: {{
                formatVersion: 1,
                entries: [{{ assetId: "startup", type: "background", url: "startup.png", phase: "critical" }}],
              }},
              context: {{}},
              startPreload,
              buildPrefetchManifest,
              now: () => nowMs,
              prefetchRetryDelayMs: 1000,
              onStatusChange(kind) {{ events.push(kind); }},
            }});

            pipeline.start();
            controllers[0].finish({{ loadedCount: 1, loadedAssetIds: ["startup"] }});
            const snapshot = {{ sceneId: "scene-1", blockId: "line-1", blockIndex: 0, choiceOptions: [] }};
            pipeline.prefetch(snapshot);
            pipeline.prefetch(snapshot);
            controllers[1].finish({{
              loadedCount: 1,
              failedCount: 1,
              loadedAssetIds: ["route-a"],
              failedAssetIds: ["route-b"],
            }});
            pipeline.prefetch(snapshot);
            const beforeRetryCount = controllers.length;
            nowMs += 1200;
            pipeline.prefetch(snapshot);
            const afterRetryCount = controllers.length;
            pipeline.prefetch({{ ...snapshot, blockId: "line-2", blockIndex: 1 }});
            const finalStatus = pipeline.getStatus();

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              requestKey: tools.buildRuntimeScenePrefetchRequestKey(snapshot),
              beforeRetryCount,
              afterRetryCount,
              totalControllerCount: controllers.length,
              oldControllerStopped: controllers[1].stopped,
              manifestCalls,
              finalStatus,
              events,
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
        self.assertIn("createRuntimeAssetPipeline", payload["keys"])
        self.assertEqual(payload["requestKey"], "scene-1:line-1:0|")
        self.assertEqual(payload["beforeRetryCount"], 2)
        self.assertEqual(payload["afterRetryCount"], 3)
        self.assertEqual(payload["totalControllerCount"], 4)
        self.assertTrue(payload["oldControllerStopped"])
        self.assertEqual(payload["manifestCalls"][0]["excluded"], ["startup"])
        self.assertEqual(payload["manifestCalls"][1]["excluded"], ["route-a", "startup"])
        self.assertIn("route-a", payload["finalStatus"]["cachedAssetIds"])
        self.assertNotIn("route-b", payload["finalStatus"]["cachedAssetIds"])
        self.assertIn("preload", payload["events"])
        self.assertIn("prefetch", payload["events"])

    def test_prefetch_reset_preserves_reusable_cache_unless_explicitly_cleared(self) -> None:
        script = textwrap.dedent(
            f"""
            import {{ createRuntimeAssetPipeline }} from {json.dumps(MODULE_PATH.as_uri())};

            const controllers = [];
            function startPreload(manifest, options) {{
              let status = {{ totalCount: manifest.entries.length, loadedAssetIds: [], skippedAssetIds: [] }};
              const controller = {{
                stop() {{}},
                getStatus() {{ return status; }},
                finish(assetId) {{
                  status = {{ ...status, loadedCount: 1, pendingCount: 0, finished: true, loadedAssetIds: [assetId] }};
                  options.onProgress(status);
                }},
              }};
              controllers.push(controller);
              return controller;
            }}
            const pipeline = createRuntimeAssetPipeline({{
              preloadManifest: {{ formatVersion: 1, entries: [] }},
              startPreload,
              buildPrefetchManifest() {{
                return {{ entries: [{{ assetId: "next", type: "background", url: "next.png" }}] }};
              }},
            }});
            pipeline.start();
            pipeline.prefetch({{ sceneId: "s", blockId: "b", blockIndex: 0 }});
            controllers[1].finish("next");
            pipeline.resetPrefetch();
            const preserved = pipeline.getStatus().cachedAssetIds;
            pipeline.resetPrefetch({{ clearCache: true }});
            const cleared = pipeline.getStatus().cachedAssetIds;
            process.stdout.write(JSON.stringify({{ preserved, cleared }}));
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
        self.assertEqual(payload["preserved"], ["next"])
        self.assertEqual(payload["cleared"], [])


if __name__ == "__main__":
    unittest.main()
