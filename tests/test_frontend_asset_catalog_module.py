from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "asset_catalog.js"


class FrontendAssetCatalogModuleTests(unittest.TestCase):
    def test_asset_catalog_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.TonyNaEditorAssetCatalog;
            const result = {{
              backgroundLabel: tools.getAssetTypeLabel("background"),
              modelLabel: tools.getAssetTypeLabel("model3d"),
              unknownLabel: tools.getAssetTypeLabel("custom"),
              videoTags: tools.getAssetPresetTags("video"),
              safePresentation: tools.getSafeCharacterPresentationMode("unknown"),
              live2dPresentation: tools.getCharacterPresentationModeLabel("live2d"),
              safeFilter: tools.getSafeAssetFilterMode(" media_budget "),
              badFilter: tools.getSafeAssetFilterMode("broken"),
              filterLabel: tools.getAssetFilterModeLabel("asset3d_risk"),
              filterStatus: tools.getAssetFilterModeStatusLabel("media_budget"),
              videoWarnBytes: tools.getAssetMediaBudgetLimit({{ type: "video" }}).warnBytes,
              missingLimit: tools.getAssetMediaBudgetLimit({{ type: "custom" }}),
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
        self.assertEqual(payload["backgroundLabel"], "背景")
        self.assertEqual(payload["modelLabel"], "3D 模型")
        self.assertEqual(payload["unknownLabel"], "custom")
        self.assertEqual(payload["videoTags"], ["OP", "ED", "PV", "过场"])
        self.assertEqual(payload["safePresentation"], "sprite")
        self.assertEqual(payload["live2dPresentation"], "Live2D")
        self.assertEqual(payload["safeFilter"], "media_budget")
        self.assertEqual(payload["badFilter"], "all")
        self.assertEqual(payload["filterLabel"], "仅看 3D 发布风险")
        self.assertIn("体积偏大", payload["filterStatus"])
        self.assertEqual(payload["videoWarnBytes"], 120 * 1024 * 1024)
        self.assertIsNone(payload["missingLimit"])


if __name__ == "__main__":
    unittest.main()
