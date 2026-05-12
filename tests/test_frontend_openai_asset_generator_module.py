from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "openai_asset_generator.js"


class FrontendOpenAiAssetGeneratorModuleTests(unittest.TestCase):
    def test_openai_asset_generator_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorOpenAiAssetGenerator;
            const state = {{
              ...tools.getDefaultOpenAiAssetGenerationState(),
              openAiAssetType: "sprite",
              openAiAssetPrompt: "原创女主角立绘",
              openAiAssetName: "女主默认",
              openAiAssetApiKey: "sk-test",
              openAiAssetModel: "gpt-image-test",
              openAiAssetSize: "1536x1024",
              openAiAssetQuality: "high",
              openAiAssetBackground: "transparent",
              openAiAssetOutputFormat: "webp",
              openAiAssetLastResult: {{ asset: {{ name: "女主默认", type: "sprite" }} }},
            }};
            const html = tools.renderOpenAiAssetGeneratorPanel({{
              state,
              selectedAssetType: "background",
              escapeHtml: (value) => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
              getAssetTypeLabel: (type) => ({{ background: "背景", sprite: "立绘", cg: "CG", ui: "界面素材" }}[type] || type),
            }});
            const result = {{
              api: tools.API_GENERATE_OPENAI_ASSET,
              defaultType: tools.getDefaultOpenAiAssetGenerationState().openAiAssetType,
              safeType: tools.getSafeOpenAiAssetGenerationType("bad"),
              safeOption: tools.getSafeOpenAiAssetGenerationOption("bad", tools.OPENAI_ASSET_GENERATION_SIZES, "1024x1024"),
              spritePrompt: tools.getOpenAiAssetPromptSample("sprite"),
              payload: tools.buildOpenAiAssetGenerationPayload(state),
              hasButton: html.includes('data-action="generate-openai-asset"'),
              hasPrivacyCopy: html.includes("不会写入项目文件"),
              hasLastResult: html.includes("女主默认"),
            }};
            console.log(JSON.stringify(result));
            """
        )
        completed = subprocess.run(["node", "-e", script], text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)

        self.assertEqual(result["api"], "/api/generate-openai-asset")
        self.assertEqual(result["defaultType"], "background")
        self.assertEqual(result["safeType"], "background")
        self.assertEqual(result["safeOption"], "1024x1024")
        self.assertIn("立绘", result["spritePrompt"])
        self.assertEqual(result["payload"]["assetType"], "sprite")
        self.assertEqual(result["payload"]["apiKey"], "sk-test")
        self.assertEqual(result["payload"]["outputFormat"], "webp")
        self.assertTrue(result["hasButton"])
        self.assertTrue(result["hasPrivacyCopy"])
        self.assertTrue(result["hasLastResult"])


if __name__ == "__main__":
    unittest.main()
