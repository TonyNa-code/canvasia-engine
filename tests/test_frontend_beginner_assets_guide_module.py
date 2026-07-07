from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "beginner_assets_guide.js"


class FrontendBeginnerAssetsGuideModuleTests(unittest.TestCase):
    def test_beginner_assets_guide_prioritizes_asset_gaps_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorBeginnerAssetsGuide;
            const helpers = {{
              escapeHtml(value) {{
                return String(value ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
              }},
              renderQuickActionButton(action, emphasized = false) {{
                const datasetMarkup = Object.entries(action.dataset ?? {{}})
                  .map(([key, value]) => ` data-${{key}}="${{value}}"`)
                  .join("");
                return `<button class="${{emphasized ? "primary" : "secondary"}}" data-action="${{action.action}}"${{datasetMarkup}}>${{action.label}}</button>`;
              }},
              renderRouteMetricCard(label, value, hint) {{
                const escape = (input) => String(input ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
                return `<metric data-label="${{escape(label)}}" data-value="${{escape(value)}}" data-hint="${{escape(hint)}}"></metric>`;
              }},
            }};
            const baseOverview = {{ readyCount: 0, missingCount: 0, urgentMissingCount: 0 }};
            const voiceModel = tools.buildBeginnerAssetsGuideModel({{
              overview: {{ ...baseOverview, missingCount: 3 }},
              selectedAssetType: "voice",
              selectedTypeLabel: "语音",
              voiceMatchTargetCount: 2,
              currentTypeSummaryText: "还有两句语音待匹配",
            }});
            const selectedMissingModel = tools.buildBeginnerAssetsGuideModel({{
              overview: {{ ...baseOverview, missingCount: 1 }},
              selectedAsset: {{ name: "女主立绘 <坏标签>", fileExists: false }},
              selectedAssetType: "sprite",
              selectedTypeLabel: "立绘",
              selectedAssetName: "女主立绘 <坏标签>",
              currentTypeSummaryText: "立绘缺真实文件",
            }});
            const urgentModel = tools.buildBeginnerAssetsGuideModel({{
              overview: {{ ...baseOverview, urgentMissingCount: 4, missingCount: 5 }},
              selectedAssetType: "background",
              selectedTypeLabel: "背景",
              currentTypeSummaryText: "背景缺口最多",
            }});
            const missingModel = tools.buildBeginnerAssetsGuideModel({{
              overview: {{ ...baseOverview, missingCount: 5 }},
              selectedAssetType: "bgm",
              selectedTypeLabel: "BGM",
              currentTypeSummaryText: "BGM 还没有文件",
            }});
            const readyModel = tools.buildBeginnerAssetsGuideModel({{
              overview: {{ readyCount: 7, missingCount: 0, urgentMissingCount: 0 }},
              selectedAssetType: "cg",
              selectedTypeLabel: "CG",
              currentTypeSummaryText: "CG 已就绪",
            }});
            const idleModel = tools.buildBeginnerAssetsGuideModel({{
              overview: baseOverview,
              selectedAssetType: "background",
              selectedTypeLabel: "背景",
              currentTypeSummaryText: "这一类暂时还没有素材",
            }});
            const html = tools.renderBeginnerAssetsGuidePanel(selectedMissingModel, helpers);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              voiceModel,
              selectedMissingModel,
              urgentModel,
              missingModel,
              readyModel,
              idleModel,
              html,
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

        self.assertIn("buildBeginnerAssetsGuideModel", payload["keys"])
        self.assertIn("renderBeginnerAssetsGuidePanel", payload["keys"])
        self.assertEqual(payload["voiceModel"]["title"], "匹配待导入语音条目")
        self.assertEqual(payload["voiceModel"]["actions"][0]["action"], "pick-voice-placeholder-files")
        self.assertEqual(payload["voiceModel"]["actions"][1]["dataset"]["asset-type"], "voice")
        self.assertEqual(payload["selectedMissingModel"]["title"], "补齐“女主立绘 <坏标签>”的真实文件")
        self.assertEqual(payload["selectedMissingModel"]["actions"][0]["action"], "replace-asset-file")
        self.assertEqual(payload["selectedMissingModel"]["actions"][1]["dataset"]["asset-type"], "sprite")
        self.assertEqual(payload["urgentModel"]["title"], "补齐已被引用的缺口素材")
        self.assertEqual(payload["urgentModel"]["actions"][0]["dataset"]["asset-filter-mode"], "urgent_missing")
        self.assertEqual(payload["missingModel"]["title"], "继续补齐待导入素材")
        self.assertEqual(payload["readyModel"]["title"], "素材基础已具备")
        self.assertEqual(payload["readyModel"]["actions"][1]["dataset"]["screen"], "preview")
        self.assertEqual(payload["idleModel"]["title"], "导入第一批素材")
        self.assertIn("新手素材顺序", payload["html"])
        self.assertIn("女主立绘 &lt;坏标签&gt;", payload["html"])
        self.assertIn('data-action="replace-asset-file"', payload["html"])
        self.assertIn("立绘缺真实文件", payload["html"])
        self.assertIn('data-label="当前分类"', payload["html"])


if __name__ == "__main__":
    unittest.main()
