from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "validation_cache.js"


class FrontendValidationCacheModuleTests(unittest.TestCase):
    def test_validation_cache_reuses_results_until_key_changes_or_forced(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            let nowValue = 100;
            const context = {{
              window: {{}},
              performance: {{
                now() {{
                  nowValue += 3;
                  return nowValue;
                }},
              }},
            }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorValidationCache;
            const cache = tools.createValidationCache();
            let computeCount = 0;
            const compute = () => {{
              computeCount += 1;
              return {{ errors: [{{ message: `error-${{computeCount}}` }}], warnings: [] }};
            }};
            const first = cache.getOrCompute("project:1", compute);
            const second = cache.getOrCompute("project:1", compute);
            const forced = cache.getOrCompute("project:1", compute, {{ force: true }});
            const nextKey = cache.getOrCompute("project:2", compute);
            cache.invalidate();
            const afterInvalidate = cache.getOrCompute("project:2", compute);
            const normalized = tools.normalizeValidationResult({{ errors: "bad", warnings: [{{ message: "ok" }}] }});
            process.stdout.write(JSON.stringify({{
              first,
              second,
              forced,
              nextKey,
              afterInvalidate,
              normalized,
              computeCount,
              stats: cache.getStats(),
              empty: tools.EMPTY_VALIDATION,
            }}));
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
        self.assertEqual(payload["computeCount"], 4)
        self.assertEqual(payload["first"]["errors"][0]["message"], "error-1")
        self.assertEqual(payload["second"]["errors"][0]["message"], "error-1")
        self.assertEqual(payload["forced"]["errors"][0]["message"], "error-2")
        self.assertEqual(payload["nextKey"]["errors"][0]["message"], "error-3")
        self.assertEqual(payload["afterInvalidate"]["errors"][0]["message"], "error-4")
        self.assertEqual(payload["normalized"]["errors"], [])
        self.assertEqual(payload["normalized"]["warnings"], [{"message": "ok"}])
        self.assertEqual(payload["empty"], {"errors": [], "warnings": []})
        self.assertEqual(payload["stats"]["hitCount"], 1)
        self.assertEqual(payload["stats"]["missCount"], 4)
        self.assertEqual(payload["stats"]["invalidationCount"], 1)
        self.assertTrue(payload["stats"]["hasEntry"])
        self.assertEqual(payload["stats"]["key"], "project:2")
        self.assertGreaterEqual(payload["stats"]["lastDurationMs"], 0)


if __name__ == "__main__":
    unittest.main()
