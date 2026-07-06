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
              phaseDelayMs: {{ early: 0, deferred: 0, library: 0 }},
              backgroundBatchDelayMs: 0,
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
        self.assertEqual(payload["status"]["readyPhases"], ["critical", "early", "deferred"])
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

    def test_runtime_preload_reuses_cached_asset_ids_without_starting_requests(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const started = [];
            class FakeImage {{
              set src(value) {{
                this._src = value;
                started.push(value.split("/").pop());
                queueMicrotask(() => this.onload?.());
              }}
              get src() {{
                return this._src;
              }}
            }}

            const manifest = {{
              formatVersion: 1,
              entries: [
                {{ assetId: "bg_cached", type: "background", url: "assets/background/cached.png", phase: "critical", priority: 100 }},
                {{ assetId: "bg_new", type: "background", url: "assets/background/new.png", phase: "critical", priority: 99 }},
              ],
            }};

            const controller = tools.startRuntimePreload(manifest, {{
              ImageCtor: FakeImage,
              skipAssetIds: new Set(["bg_cached"]),
              timeoutMs: 500,
            }});

            await new Promise((resolve) => setTimeout(resolve, 0));
            await new Promise((resolve) => setTimeout(resolve, 0));

            process.stdout.write(JSON.stringify({{
              started,
              status: controller.getStatus(),
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
        self.assertEqual(payload["started"], ["new.png"])
        self.assertEqual(payload["status"]["totalCount"], 2)
        self.assertEqual(payload["status"]["queuedCount"], 1)
        self.assertEqual(payload["status"]["loadedCount"], 1)
        self.assertEqual(payload["status"]["skippedCount"], 1)
        self.assertEqual(payload["status"]["readyCount"], 2)
        self.assertEqual(payload["status"]["loadedAssetIds"], ["bg_new"])
        self.assertEqual(payload["status"]["skippedAssetIds"], ["bg_cached"])
        self.assertTrue(payload["status"]["finished"])

    def test_runtime_preload_cache_efficiency_summary_combines_preload_and_prefetch_status(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const empty = tools.buildRuntimePreloadCacheEfficiencySummary(null);
            const mixed = tools.buildRuntimePreloadCacheEfficiencySummary({{
              preloadStatus: {{
                totalCount: 3,
                readyCount: 2,
                pendingCount: 1,
                skippedCount: 1,
              }},
              prefetchStatus: {{
                totalCount: 2,
                loadedCount: 2,
                pendingCount: 0,
                skippedCount: 1,
              }},
            }});
            const aliasInput = tools.buildRuntimePreloadCacheEfficiencySummary({{
              runtimePreloadStatus: {{ totalCount: 1, loadedCount: 1, skippedCount: 0 }},
              runtimeScenePrefetchStatus: {{ totalCount: 1, readyCount: 0, pendingCount: 1, skippedCount: 0 }},
            }});

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              empty,
              mixed,
              aliasInput,
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
        self.assertIn("buildRuntimePreloadCacheEfficiencySummary", payload["keys"])
        self.assertEqual(payload["empty"]["status"], "empty")
        self.assertEqual(payload["mixed"]["status"], "warming")
        self.assertEqual(payload["mixed"]["totalCount"], 5)
        self.assertEqual(payload["mixed"]["readyCount"], 4)
        self.assertEqual(payload["mixed"]["pendingCount"], 1)
        self.assertEqual(payload["mixed"]["skippedCount"], 2)
        self.assertEqual(payload["mixed"]["readyPercent"], 80)
        self.assertEqual(payload["mixed"]["reusePercent"], 40)
        self.assertEqual(payload["mixed"]["preloadSkippedCount"], 1)
        self.assertEqual(payload["mixed"]["prefetchSkippedCount"], 1)
        self.assertEqual(payload["aliasInput"]["status"], "warming")
        self.assertEqual(payload["aliasInput"]["readyPercent"], 50)

    def test_runtime_preload_stages_background_phases_and_batches_work(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const pending = [];
            const started = [];

            function wait(ms) {{
              return new Promise((resolve) => setTimeout(resolve, ms));
            }}

            class SlowImage {{
              set src(value) {{
                this._src = value;
                started.push(value.split("/").pop());
                pending.push(() => this.onload?.());
              }}
              get src() {{
                return this._src;
              }}
            }}

            const manifest = {{
              formatVersion: 1,
              entries: [
                {{ assetId: "critical", type: "background", url: "assets/background/critical.png", phase: "critical", priority: 100 }},
                {{ assetId: "early_a", type: "background", url: "assets/background/early-a.png", phase: "early", priority: 72 }},
                {{ assetId: "early_b", type: "background", url: "assets/background/early-b.png", phase: "early", priority: 71 }},
                {{ assetId: "deferred", type: "background", url: "assets/background/deferred.png", phase: "deferred", priority: 38 }},
                {{ assetId: "library", type: "background", url: "assets/background/library.png", phase: "library", priority: 18 }},
              ],
            }};

            const controller = tools.startRuntimePreload(manifest, {{
              ImageCtor: SlowImage,
              maxConcurrent: 4,
              backgroundBatchSize: 1,
              backgroundBatchDelayMs: 8,
              phaseDelayMs: {{ early: 0, deferred: 24, library: 52 }},
              requestIdleCallback(callback) {{ callback(); }},
              timeoutMs: 500,
            }});

            await wait(0);
            const immediateStarted = [...started];
            const immediateStatus = controller.getStatus();

            pending.shift()?.();
            await wait(10);
            const afterFirstBackgroundBatch = [...started];

            while (pending.length) {{
              pending.shift()?.();
              await wait(0);
            }}
            await wait(28);
            const afterDeferredDelay = [...started];
            const afterDeferredStatus = controller.getStatus();

            while (pending.length) {{
              pending.shift()?.();
              await wait(0);
            }}
            await wait(36);
            const afterLibraryDelay = [...started];
            const afterLibraryStatus = controller.getStatus();

            process.stdout.write(JSON.stringify({{
              immediateStarted,
              immediateStatus,
              afterFirstBackgroundBatch,
              afterDeferredDelay,
              afterDeferredStatus,
              afterLibraryDelay,
              afterLibraryStatus,
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
        self.assertEqual(payload["immediateStarted"], ["critical.png", "early-a.png"])
        self.assertEqual(payload["immediateStatus"]["readyPhases"], ["critical", "early"])
        self.assertNotIn("early-b.png", payload["immediateStarted"])
        self.assertIn("early-b.png", payload["afterFirstBackgroundBatch"])
        self.assertNotIn("deferred.png", payload["afterFirstBackgroundBatch"])
        self.assertIn("deferred.png", payload["afterDeferredDelay"])
        self.assertEqual(payload["afterDeferredStatus"]["readyPhases"], ["critical", "early", "deferred"])
        self.assertNotIn("library.png", payload["afterDeferredDelay"])
        self.assertIn("library.png", payload["afterLibraryDelay"])
        self.assertEqual(payload["afterLibraryStatus"]["readyPhases"], ["critical", "early", "deferred", "library"])

    def test_runtime_preload_applies_project_performance_profiles(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const started = [];
            const pending = [];

            class SlowImage {{
              set src(value) {{
                this._src = value;
                started.push(value);
                pending.push(() => this.onload?.());
              }}
              get src() {{
                return this._src;
              }}
            }}

            const manifest = {{
              formatVersion: 1,
              entries: [
                {{ assetId: "a", type: "background", url: "a.png", phase: "critical", priority: 10 }},
                {{ assetId: "b", type: "background", url: "b.png", phase: "critical", priority: 9 }},
                {{ assetId: "c", type: "background", url: "c.png", phase: "critical", priority: 8 }},
                {{ assetId: "d", type: "background", url: "d.png", phase: "critical", priority: 7 }},
                {{ assetId: "e", type: "background", url: "e.png", phase: "critical", priority: 6 }},
                {{ assetId: "f", type: "background", url: "f.png", phase: "critical", priority: 5 }},
              ],
            }};

            const mobileOptions = tools.resolveRuntimePreloadOptions({{
              runtimeSettings: {{ performanceProfile: "mobile_low" }},
            }});
            const highQualityOptions = tools.resolveRuntimePreloadOptions({{
              project: {{ runtimeSettings: {{ performanceProfile: "high_quality_pc" }} }},
            }});
            const fallbackOptions = tools.resolveRuntimePreloadOptions({{
              runtimeSettings: {{ performanceProfile: "bad-profile" }},
            }});
            const legacyDelayOptions = tools.resolveRuntimePreloadOptions({{
              runtimeSettings: {{ performanceProfile: "web" }},
              deferredDelayMs: 777,
            }});

            const controller = tools.startRuntimePreload(manifest, {{
              runtimeSettings: {{ performanceProfile: "mobile_low" }},
              ImageCtor: SlowImage,
              requestIdleCallback() {{}},
              timeoutMs: 500,
              deferredDelayMs: 0,
            }});
            await new Promise((resolve) => setTimeout(resolve, 0));
            const status = controller.getStatus();
            const startedBeforeRelease = [...started];
            for (let index = 0; index < 6; index += 1) {{
              while (pending.length) {{
                pending.shift()?.();
              }}
              await new Promise((resolve) => setTimeout(resolve, 0));
              if (controller.getStatus().loadedCount >= manifest.entries.length) {{
                break;
              }}
            }}

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              mobileOptions,
              highQualityOptions,
              fallbackOptions,
              legacyDelayOptions,
              status,
              startedCount: startedBeforeRelease.length,
              started: startedBeforeRelease,
              safeProfiles: [
                tools.getSafeRuntimePreloadPerformanceProfile("web"),
                tools.getSafeRuntimePreloadPerformanceProfile("missing"),
              ],
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
        self.assertIn("resolveRuntimePreloadOptions", payload["keys"])
        self.assertIn("getSafeRuntimePreloadPerformanceProfile", payload["keys"])
        self.assertEqual(payload["mobileOptions"]["performanceProfile"], "mobile_low")
        self.assertEqual(payload["mobileOptions"]["maxConcurrent"], 2)
        self.assertEqual(payload["mobileOptions"]["deferredDelayMs"], 360)
        self.assertEqual(payload["mobileOptions"]["backgroundBatchSize"], 1)
        self.assertEqual(payload["mobileOptions"]["phaseDelayMs"]["library"], 8000)
        self.assertEqual(payload["highQualityOptions"]["performanceProfile"], "high_quality_pc")
        self.assertEqual(payload["highQualityOptions"]["maxConcurrent"], 6)
        self.assertEqual(payload["highQualityOptions"]["backgroundBatchSize"], 5)
        self.assertEqual(payload["highQualityOptions"]["phaseDelayMs"]["deferred"], 420)
        self.assertEqual(payload["fallbackOptions"]["performanceProfile"], "standard")
        self.assertEqual(payload["legacyDelayOptions"]["deferredDelayMs"], 777)
        self.assertEqual(payload["legacyDelayOptions"]["phaseDelayMs"], {"early": 777, "deferred": 777, "library": 777})
        self.assertEqual(payload["status"]["performanceProfile"], "mobile_low")
        self.assertEqual(payload["status"]["performanceProfileLabel"], "低配 / 移动端")
        self.assertEqual(payload["status"]["maxConcurrent"], 2)
        self.assertEqual(payload["startedCount"], 2)
        self.assertEqual(payload["safeProfiles"], ["web", "standard"])


if __name__ == "__main__":
    unittest.main()
