from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "script_importer_panel.js"


class FrontendScriptImporterPanelModuleTests(unittest.TestCase):
    def test_script_importer_panel_renders_preview_and_supported_syntax_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorScriptImporterPanel;
            const scriptImporterTools = {{
              summarizeScriptDraftBlocks(blocks) {{
                return {{
                  total: blocks.length,
                  dialogue: blocks.filter((block) => block.type === "dialogue").length,
                  narration: blocks.filter((block) => block.type === "narration").length,
                  choice: blocks.filter((block) => block.type === "choice").length,
                  stage: blocks.filter((block) => block.type === "background" || block.type === "music_play").length,
                  logic: blocks.filter((block) => block.type === "variable_set").length,
                  route: blocks.filter((block) => block.type === "jump").length,
                }};
              }},
              buildScriptDraftPreviewLines(blocks, limit) {{
                return blocks.slice(0, limit).map((block, index) => `${{index + 1}}:${{block.type}}:${{block.text ?? block.assetHint ?? ""}}`);
              }},
            }};
            const blocks = [
              {{ type: "dialogue", text: "你好 <世界>" }},
              {{ type: "narration", text: "雨声" }},
              {{ type: "choice", options: [] }},
              {{ type: "background", assetHint: "classroom" }},
              {{ type: "music_play", assetHint: "theme" }},
              {{ type: "variable_set" }},
              {{ type: "jump" }},
            ];
            const sample = tools.getScriptImporterSampleDraft("悠奈");
            const emptySummary = tools.getScriptImportSummaryText([], {{ scriptImporterTools }});
            const summary = tools.getScriptImportSummaryText(blocks, {{ scriptImporterTools }});
            const insertedSummary = tools.getScriptImportInsertedSummaryText(blocks, {{ scriptImporterTools }});
            const emptyInsertedSummary = tools.getScriptImportInsertedSummaryText([], {{ scriptImporterTools }});
            const capabilityGrid = tools.renderScriptImporterCapabilityGrid();
            const html = tools.renderScriptImporterPanel({{ id: "scene_1" }}, null, {{
              blocks,
              draft: '悠奈 "你好 <世界>"',
              error: "有一行没识别",
              insertionTarget: "当前会插入到「第一句」后面",
              scriptImporterTools,
            }});
            const emptyHtml = tools.renderScriptImporterPanel({{ id: "scene_1" }}, null, {{
              blocks: [],
              draft: "",
              scriptImporterTools,
            }});
            const noSceneHtml = tools.renderScriptImporterPanel(null, null, {{ scriptImporterTools }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              sample,
              emptySummary,
              summary,
              insertedSummary,
              emptyInsertedSummary,
              capabilityGroups: tools.getScriptImporterCapabilityGroups(),
              capabilityGrid,
              html,
              emptyHtml,
              noSceneHtml,
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
        html = payload["html"]

        self.assertIn("renderScriptImporterPanel", payload["keys"])
        self.assertIn("getScriptImportInsertedSummaryText", payload["keys"])
        self.assertIn("getScriptImporterSampleDraft", payload["keys"])
        self.assertIn("show 悠奈 smile at center", payload["sample"])
        self.assertEqual(payload["emptySummary"], "还没有预览结果")
        self.assertEqual(payload["summary"], "将插入 7 张卡片：台词 1 / 旁白 1 / 选项 1 / 演出 2 / 逻辑 1 / 跳转 1")
        self.assertEqual(payload["insertedSummary"], "已插入 7 张剧情卡片：台词 1 / 旁白 1 / 选项 1 / 演出 2 / 逻辑 1 / 跳转 1")
        self.assertEqual(payload["emptyInsertedSummary"], "没有可插入的剧情卡片")
        self.assertEqual(payload["capabilityGroups"][0]["title"], "正文")
        self.assertIn("script-importer-capability-grid", payload["capabilityGrid"])
        self.assertIn("Text To Cards", html)
        self.assertIn("当前会插入到「第一句」后面", html)
        self.assertIn("角色台词", html)
        self.assertIn("script-importer-capability-card", html)
        self.assertIn('data-action="preview-script-import"', html)
        self.assertIn('data-action="insert-script-import-blocks"', html)
        self.assertIn("1:dialogue:你好 &lt;世界&gt;", html)
        self.assertIn("有一行没识别", html)
        self.assertIn("悠奈 &quot;你好 &lt;世界&gt;&quot;", html)
        self.assertIn("disabled", payload["emptyHtml"])
        self.assertEqual(payload["noSceneHtml"], "")


if __name__ == "__main__":
    unittest.main()
