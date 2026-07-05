from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "asset_footprint.js"


class FrontendAssetFootprintModuleTests(unittest.TestCase):
    def test_asset_footprint_report_marks_release_size_risks(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorAssetFootprint;
            const mb = 1024 * 1024;
            const data = {{
              assetList: [
                {{ id: "op", type: "video", name: "OP 动画", fileExists: true, fileSizeBytes: 620 * mb, path: "video/op.mp4" }},
                {{ id: "bgm", type: "bgm", name: "主旋律", fileExists: true, fileSizeBytes: 92 * mb, path: "audio/theme.wav" }},
                {{ id: "cg", type: "cg", name: "告白 CG", fileExists: true, fileSize: "35,000,000", tags: ["主线"] }},
                {{ id: "sprite", type: "sprite", name: "女主占位立绘", fileExists: true, fileSizeBytes: 0, tags: ["占位素材"] }},
                {{ id: "room3d", type: "scene3d", name: "3D 教室", fileExists: true, sizeBytes: 130 * mb }},
                {{ id: "spare", type: "ui", name: "备用按钮", fileExists: true, fileSizeBytes: 12 * mb }},
              ],
            }};
            const report = tools.buildAssetFootprintReport(data, {{
              unusedAssetIds: new Set(["spare"]),
              totalWarnBytes: 200 * mb,
              totalDangerBytes: 850 * mb,
            }});
            const digest = tools.getAssetFootprintDigest(report);
            const markdown = tools.buildAssetFootprintMarkdown(report, {{
              projectTitle: "心跳时差",
              generatedAt: "2026-07-05",
            }});
            const csv = tools.buildAssetFootprintCsv(report);
            console.log(JSON.stringify({{
              totalLabel: report.totals.totalLabel,
              releaseRiskLevel: report.releaseRiskLevel,
              warningCodes: report.warnings.map((warning) => warning.code),
              topIds: report.topAssets.slice(0, 3).map((asset) => asset.id),
              categoryRows: report.categories.map((category) => [category.category, category.count, category.riskCount]),
              digest,
              markdownHasSections: [
                markdown.includes("# 心跳时差 素材体积雷达"),
                markdown.includes("## 分类体积"),
                markdown.includes("OP 动画"),
              ],
              csvHasRows: [
                csv.startsWith("\\uFEFF"),
                csv.includes("OP 动画"),
                csv.includes("未使用"),
              ],
              normalizedSizes: [
                tools.normalizeAssetSizeBytes({{ fileSize: "1,024" }}),
                tools.normalizeAssetSizeBytes({{ fileSize: "1.5 MB" }}),
                tools.normalizeAssetSizeBytes({{ sizeBytes: -1 }}),
              ],
              categories: [
                tools.getAssetFootprintCategory({{ type: "background" }}),
                tools.getAssetFootprintCategory({{ type: "voice" }}),
                tools.getAssetFootprintCategory({{ type: "scene3d" }}),
                tools.getAssetFootprintCategory({{ type: "unknown" }}),
              ],
            }}));
            """
        )
        result = subprocess.run(
            ["node", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(payload["releaseRiskLevel"], "danger")
        self.assertIn("total_footprint_danger", payload["warningCodes"])
        self.assertIn("missing_size_metadata", payload["warningCodes"])
        self.assertIn("large_unused_assets", payload["warningCodes"])
        self.assertIn("placeholder_assets", payload["warningCodes"])
        self.assertEqual(payload["topIds"][0], "op")
        self.assertIn(["video", 1, 1], payload["categoryRows"])
        self.assertIn(["audio", 1, 1], payload["categoryRows"])
        self.assertEqual(payload["digest"]["level"], "danger")
        self.assertEqual(payload["digest"]["title"], "包体风险偏高")
        self.assertTrue(all(payload["markdownHasSections"]))
        self.assertTrue(all(payload["csvHasRows"]))
        self.assertEqual(payload["normalizedSizes"], [1024, 1572864, 0])
        self.assertEqual(payload["categories"], ["image", "audio", "model3d", "other"])


if __name__ == "__main__":
    unittest.main()
