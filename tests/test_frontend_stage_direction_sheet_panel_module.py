from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_COMMON_PATH = ROOT_DIR / "prototype_editor" / "modules" / "editor_common.js"
STAGE_SHEET_PATH = ROOT_DIR / "prototype_editor" / "modules" / "stage_direction_sheet.js"
PANEL_PATH = ROOT_DIR / "prototype_editor" / "modules" / "stage_direction_sheet_panel.js"


class FrontendStageDirectionSheetPanelModuleTests(unittest.TestCase):
    def test_stage_direction_panel_renders_autofix_preview_and_empty_state(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            for (const filePath of [
              {json.dumps(str(EDITOR_COMMON_PATH))},
              {json.dumps(str(STAGE_SHEET_PATH))},
              {json.dumps(str(PANEL_PATH))},
            ]) {{
              vm.runInContext(fs.readFileSync(filePath, "utf8"), context);
            }}
            const sheetTools = context.window.CanvasiaEditorStageDirectionSheet;
            const panelTools = context.window.CanvasiaEditorStageDirectionSheetPanel;
            const data = {{
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              assetList: [
                {{ id: "sprite_hero", type: "sprite", name: "女主微笑", fileExists: true }},
              ],
              characters: [
                {{ id: "hero", displayName: "蓝白女主", defaultPosition: "left", defaultSpriteId: "sprite_hero" }},
              ],
              scenes: [
                {{
                  id: "scene_start",
                  chapterId: "chapter_1",
                  name: "教室黄昏",
                  blocks: [
                    {{ id: "line_1", type: "dialogue", speakerId: "hero", text: "今天也留下来吗？" }},
                    {{ id: "show_1", type: "character_show", characterId: "hero", transition: "none", transitionDurationMs: 0 }},
                  ],
                }},
              ],
            }};
            const sheet = sheetTools.buildStageDirectionSheet(data);
            const emptyHtml = panelTools.renderStageDirectionSheetPanel({{ summary: {{}}, issues: [], events: [] }});
            const panelHtml = panelTools.renderStageDirectionSheetPanel(sheet);
            const fixedHtml = panelTools.renderStageDirectionSheetPanel({{
              ...sheet,
              autoFixPlan: {{ changed: false, operationCount: 0, changedSceneCount: 0, changedBlockCount: 0, scenePlans: [] }},
              summary: {{ ...sheet.summary, autoFixOperationCount: 0 }},
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(panelTools).sort(),
              operationRows: panelTools.getStageAutoFixOperationRows(sheet.autoFixPlan, 4),
              emptyHtml,
              panelHtml,
              fixedHtml,
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
        self.assertIn("renderStageDirectionSheetPanel", payload["keys"])
        self.assertIn("renderStageDirectionAutoFixPreview", payload["keys"])
        self.assertIn("renderStageDirectionAutoFixButton", payload["keys"])
        self.assertIn("getStageAutoFixOperationRows", payload["keys"])
        self.assertGreaterEqual(len(payload["operationRows"]), 1)
        self.assertIn("教室黄昏", payload["panelHtml"])
        self.assertIn('data-inspection-section="stage-direction"', payload["panelHtml"])
        self.assertIn("自动补齐预览", payload["panelHtml"])
        self.assertIn("补登场转场", payload["panelHtml"])
        self.assertIn("补立绘舞台参数", payload["panelHtml"])
        self.assertIn('data-action="apply-stage-direction-autofix"', payload["panelHtml"])
        self.assertIn("补齐", payload["panelHtml"])
        self.assertIn("结尾仍在场", payload["panelHtml"])
        self.assertIn("舞台基础参数已完整", payload["fixedHtml"])
        self.assertIn('disabled aria-disabled="true"', payload["fixedHtml"])
        self.assertNotIn("自动补齐预览", payload["fixedHtml"])
        self.assertIn("当前项目还没有可列出的角色舞台事件", payload["emptyHtml"])


if __name__ == "__main__":
    unittest.main()
