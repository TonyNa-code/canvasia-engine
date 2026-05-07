from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "recent_workspace.js"


class FrontendRecentWorkspaceModuleTests(unittest.TestCase):
    def test_recent_workspace_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.TonyNaEditorRecentWorkspace;
            const storage = {{
              values: new Map(),
              getItem(key) {{
                return this.values.has(key) ? this.values.get(key) : null;
              }},
              setItem(key, value) {{
                this.values.set(key, String(value));
              }},
              removeItem(key) {{
                this.values.delete(key);
              }},
            }};
            const failingStorage = {{
              getItem() {{
                throw new Error("blocked");
              }},
              setItem() {{
                throw new Error("blocked");
              }},
              removeItem() {{
                throw new Error("blocked");
              }},
            }};
            const nowIso = () => "2026-05-07T00:00:00.000Z";
            const longTitle = "标题".repeat(120);
            const sceneEntry = tools.sanitizeRecentWorkspaceEntry({{
              type: "scene",
              sceneId: " scene_a ",
              updatedAt: "bad-date",
              title: longTitle,
              subtitle: "  第一章 · 教室  ",
              summary: "  继续写这里  ",
            }}, {{ nowIso }});
            const scriptEntry = tools.sanitizeRecentWorkspaceEntry({{
              type: "script",
              sceneId: "scene_a",
              blockId: " block_1 ",
              updatedAt: "2026-05-06T12:00:00.000Z",
            }}, {{ nowIso }});
            const assetEntry = tools.sanitizeRecentWorkspaceEntry({{
              type: "asset",
              assetId: "asset_1",
            }}, {{ nowIso }});
            const characterEntry = tools.sanitizeRecentWorkspaceEntry({{
              type: "character",
              characterId: "heroine",
            }}, {{ nowIso }});
            const merged = tools.mergeRecentWorkspaceItem(
              [sceneEntry, scriptEntry, assetEntry],
              {{
                type: "scene",
                sceneId: "scene_a",
                updatedAt: "2026-05-07T08:00:00.000Z",
                title: "重新打开的场景",
              }},
              {{ limit: 3, nowIso }}
            );
            const zeroLimit = tools.mergeRecentWorkspaceItem([sceneEntry], {{
              type: "asset",
              assetId: "asset_2",
            }}, {{ limit: 0, nowIso }});
            const key = tools.getRecentWorkspaceStorageKey("project-alpha");
            const persisted = tools.persistRecentWorkspaceItems(storage, key, [characterEntry, ...merged], {{ limit: 3 }});
            const loaded = tools.loadStoredRecentWorkspaceItems(storage, key, {{ limit: 8 }});
            const cleared = tools.clearStoredRecentWorkspaceItems(storage, key);
            const removedAfterClear = storage.getItem(key);
            storage.setItem(key, JSON.stringify({{ items: [sceneEntry, null, {{ type: "asset" }}] }}));
            const loadedFromWrappedPayload = tools.loadStoredRecentWorkspaceItems(storage, key, {{ limit: 8 }});
            const result = {{
              keys: Object.keys(tools).sort(),
              constants: [tools.RECENT_WORKSPACE_LIMIT, tools.RECENT_WORKSPACE_TYPE_LABELS.scene],
              labels: [
                tools.getRecentWorkspaceTypeLabel("scene"),
                tools.getRecentWorkspaceTypeLabel("script"),
                tools.getRecentWorkspaceTypeLabel("bad"),
              ],
              safeTypes: [
                tools.getSafeRecentWorkspaceType("asset"),
                tools.getSafeRecentWorkspaceType("unknown"),
              ],
              storageKey: key,
              sceneEntry,
              scriptEntry,
              assetEntry,
              characterEntry,
              invalidEntries: [
                tools.sanitizeRecentWorkspaceEntry(null),
                tools.sanitizeRecentWorkspaceEntry({{ type: "script", sceneId: "scene_a" }}),
                tools.sanitizeRecentWorkspaceEntry({{ type: "asset" }}),
              ],
              itemKeys: [
                tools.getRecentWorkspaceItemKey(sceneEntry),
                tools.getRecentWorkspaceItemKey(scriptEntry),
                tools.getRecentWorkspaceItemKey(assetEntry),
                tools.getRecentWorkspaceItemKey(characterEntry),
              ],
              merged,
              zeroLimit,
              persisted,
              loaded,
              cleared,
              removedAfterClear,
              loadedFromWrappedPayload,
              failingLoad: tools.loadStoredRecentWorkspaceItems(failingStorage, key),
              failingPersist: tools.persistRecentWorkspaceItems(failingStorage, key, [sceneEntry]),
              failingClear: tools.clearStoredRecentWorkspaceItems(failingStorage, key),
              textLimits: [
                tools.sanitizeRecentWorkspaceText("  abcdef  ", 3),
                tools.sanitizeRecentWorkspaceText("abcdef", 0),
                tools.sanitizeRecentWorkspaceText("abcdef", "bad"),
              ],
            }};
            process.stdout.write(JSON.stringify(result));
            """
        )
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("mergeRecentWorkspaceItem", payload["keys"])
        self.assertEqual(payload["constants"], [8, "剧情场景"])
        self.assertEqual(payload["labels"], ["剧情场景", "台本入口", "剧情场景"])
        self.assertEqual(payload["safeTypes"], ["asset", "scene"])
        self.assertEqual(payload["storageKey"], "tony-na-engine:editor-recent-work:project-alpha")
        self.assertEqual(payload["sceneEntry"]["sceneId"], "scene_a")
        self.assertEqual(payload["sceneEntry"]["updatedAt"], "2026-05-07T00:00:00.000Z")
        self.assertEqual(len(payload["sceneEntry"]["title"]), 160)
        self.assertEqual(payload["scriptEntry"]["blockId"], "block_1")
        self.assertEqual(payload["assetEntry"]["assetId"], "asset_1")
        self.assertEqual(payload["characterEntry"]["characterId"], "heroine")
        self.assertEqual(payload["invalidEntries"], [None, None, None])
        self.assertEqual(payload["itemKeys"], [
            "scene:scene_a",
            "script:scene_a:block_1",
            "asset:asset_1",
            "character:heroine",
        ])
        self.assertEqual([entry["title"] for entry in payload["merged"]], ["重新打开的场景", "", ""])
        self.assertEqual([entry["type"] for entry in payload["merged"]], ["scene", "script", "asset"])
        self.assertEqual(payload["zeroLimit"], [])
        self.assertTrue(payload["persisted"])
        self.assertEqual(len(payload["loaded"]), 3)
        self.assertEqual(payload["loaded"][0]["type"], "character")
        self.assertTrue(payload["cleared"])
        self.assertIsNone(payload["removedAfterClear"])
        self.assertEqual(len(payload["loadedFromWrappedPayload"]), 1)
        self.assertEqual(payload["failingLoad"], [])
        self.assertFalse(payload["failingPersist"])
        self.assertFalse(payload["failingClear"])
        self.assertEqual(payload["textLimits"], ["abc", "", "abcdef"])


if __name__ == "__main__":
    unittest.main()
