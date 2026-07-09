from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_storage.js"


class FrontendRuntimeStorageModuleTests(unittest.TestCase):
    def test_runtime_storage_keys_and_safe_json_helpers(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

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
            const throwingWindow = Object.create(null);
            Object.defineProperty(throwingWindow, "localStorage", {{
              get() {{
                throw new Error("blocked");
              }},
            }});
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

            const keys = tools.buildRuntimeStorageKeys({{ title: "My VN: 夏 / Demo!!" }});
            const saved = tools.writeRuntimeStorageJson(keys.quickSave, {{ sceneId: "scene_a", step: 3 }}, {{ storage }});
            const loaded = tools.readRuntimeStorageJson(keys.quickSave, null, {{ storage }});
            storage.setItem(keys.readHistory, "{{bad json");
            const badJsonFallback = tools.readRuntimeStorageJson(keys.readHistory, ["fallback"], {{ storage }});
            const removed = tools.removeRuntimeStorageItem(keys.quickSave, {{ storage }});
            const removedValue = storage.getItem(keys.quickSave);

            process.stdout.write(JSON.stringify({{
              exportedKeys: Object.keys(tools).sort(),
              suffixKeys: Object.keys(tools.RUNTIME_STORAGE_KEY_SUFFIXES).sort(),
              scope: keys.scope,
              storageKey: keys.quickSave,
              playbackKey: keys.playback,
              saved,
              loaded,
              badJsonFallback,
              removed,
              removedValue,
              emptyScope: tools.getProjectStorageScope({{ title: "   " }}),
              fallbackRead: tools.readRuntimeStorageJson(keys.playback, "fallback", {{ storage: failingStorage }}),
              fallbackWrite: tools.writeRuntimeStorageJson(keys.playback, {{}}, {{ storage: failingStorage }}),
              fallbackRemove: tools.removeRuntimeStorageItem(keys.playback, {{ storage: failingStorage }}),
              blockedBrowserStorage: tools.getBrowserStorage(throwingWindow),
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
        self.assertIn("buildRuntimeStorageKeys", payload["exportedKeys"])
        self.assertIn("readRuntimeStorageJson", payload["exportedKeys"])
        self.assertIn("writeRuntimeStorageJson", payload["exportedKeys"])
        self.assertIn("removeRuntimeStorageItem", payload["exportedKeys"])
        self.assertIn("quickSave", payload["suffixKeys"])
        self.assertIn("readHistory", payload["suffixKeys"])
        self.assertTrue(payload["scope"].startswith("my-vn"))
        self.assertIn("夏", payload["scope"])
        self.assertNotIn(" ", payload["scope"])
        self.assertNotIn(":", payload["scope"])
        self.assertTrue(payload["storageKey"].startswith("canvasia-engine:player-quicksave:"))
        self.assertTrue(payload["playbackKey"].startswith("canvasia-engine:player-preview:"))
        self.assertTrue(payload["saved"])
        self.assertEqual(payload["loaded"], {"sceneId": "scene_a", "step": 3})
        self.assertEqual(payload["badJsonFallback"], ["fallback"])
        self.assertTrue(payload["removed"])
        self.assertIsNone(payload["removedValue"])
        self.assertEqual(payload["emptyScope"], "project")
        self.assertEqual(payload["fallbackRead"], "fallback")
        self.assertFalse(payload["fallbackWrite"])
        self.assertFalse(payload["fallbackRemove"])
        self.assertIsNone(payload["blockedBrowserStorage"])


if __name__ == "__main__":
    unittest.main()
