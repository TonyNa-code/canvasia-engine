from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "character_presentation_panel.js"


class FrontendCharacterPresentationPanelModuleTests(unittest.TestCase):
    def test_character_presentation_panel_renders_bindings_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorCharacterPresentationPanel;
            const helpers = {{
              escapeHtml(value) {{
                return String(value ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
              }},
              buildGameUiAssetSelectOptions(selectedValue, types, emptyLabel) {{
                return `<option value="">${{emptyLabel}}</option><option value="${{selectedValue}}" selected>${{types.join("+")}}:${{selectedValue}}</option>`;
              }},
              getCharacterPresentationModeLabel(character) {{
                return character.presentationLabel ?? "Live2D";
              }},
              renderStatCard(label, value) {{
                const escape = (input) => String(input ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
                return `<stat data-label="${{escape(label)}}" data-value="${{escape(value)}}"></stat>`;
              }},
              getCharacterExpressionBindingStatus(expression) {{
                return expression.live2dExpression || expression.model3dAnimation
                  ? {{ tone: "good-text", label: "已绑定" }}
                  : {{ tone: "warn-text", label: "待绑定" }};
              }},
            }};
            const character = {{
              id: "char_1",
              presentationLabel: "Live2D",
              expressions: [
                {{
                  id: "smile",
                  name: "微笑 <tag>",
                  layerAssetIds: ["eye", "mouth"],
                  live2dExpression: "smile.exp3.json",
                  live2dMotion: "tap_body.motion3.json",
                  model3dExpression: "joy",
                  model3dAnimation: "Wave",
                }},
                {{
                  id: "sad",
                  name: "低落",
                  layerAssetIds: [],
                }},
              ],
            }};
            const readiness = {{
              score: 82,
              tone: "good-text",
              primaryHealth: {{ ok: true, label: "Live2D 可用", asset: {{ id: "live2d_1" }} }},
              fallbackHealth: {{ ok: false, label: "缺少兜底", asset: {{ id: "sprite_1" }} }},
              mappedExpressionCount: 1,
              expressionCount: 2,
              issues: [
                {{ tone: "warn-text", title: "缺少兜底", detail: "建议补一张普通立绘兜底。" }},
              ],
            }};
            const model = {{
              character,
              presentation: {{
                mode: "live2d",
                fallbackSpriteAssetId: "sprite_1",
                live2d: {{
                  modelAssetId: "live2d_1",
                  idleMotion: "Idle <unsafe>",
                  blink: true,
                  breath: true,
                  lipSync: false,
                  cursorTracking: true,
                }},
                model3d: {{
                  modelAssetId: "model3d_1",
                  idleAnimation: "Stand",
                }},
              }},
              status: {{ tone: "good-text", label: "已配置", detail: "可以进入预览。" }},
              readiness,
              boundAssetNames: "Live2D 模型 / 兜底立绘",
              modeLabels: {{
                sprite: "普通立绘",
                layered_sprite: "差分立绘",
                live2d: "Live2D",
                model3d: "3D 模型",
              }},
            }};
            const panelHtml = tools.renderCharacterPresentationPanel(model, helpers);
            const readinessCleanHtml = tools.renderCharacterPresentationReadinessPanel(character, {{
              score: 100,
              tone: "good-text",
              primaryHealth: {{ ok: true, label: "主素材可用" }},
              fallbackHealth: {{ ok: true, label: "兜底安全" }},
              mappedExpressionCount: 2,
              expressionCount: 2,
              issues: [],
            }}, helpers);
            const emptyExpressionHtml = tools.renderCharacterExpressionBindingPanel({{ expressions: [] }}, helpers);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              panelHtml,
              readinessCleanHtml,
              emptyExpressionHtml,
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
        panel_html = payload["panelHtml"]

        self.assertIn("renderCharacterPresentationPanel", payload["keys"])
        self.assertIn("renderCharacterExpressionBindingPanel", payload["keys"])
        self.assertIn("高级角色表现", panel_html)
        self.assertIn("Live2D 模型入口", panel_html)
        self.assertIn("3D 模型入口", panel_html)
        self.assertIn('id="characterPresentationModeSelect"', panel_html)
        self.assertIn('value="live2d" selected', panel_html)
        self.assertIn("Idle &lt;unsafe&gt;", panel_html)
        self.assertIn("自动眨眼", panel_html)
        self.assertIn("口型同步", panel_html)
        self.assertIn("已纳入引用保护：Live2D 模型 / 兜底立绘", panel_html)
        self.assertIn("角色表现体检 82%", panel_html)
        self.assertIn('data-label="表情映射"', panel_html)
        self.assertIn("缺少兜底", panel_html)
        self.assertIn("表情级映射", panel_html)
        self.assertIn('data-expression-id="smile"', panel_html)
        self.assertIn("微笑 &lt;tag&gt;", panel_html)
        self.assertIn("smile.exp3.json", panel_html)
        self.assertIn("Wave", panel_html)
        self.assertIn('data-action="save-character-presentation"', panel_html)
        self.assertIn('data-character-id="char_1"', panel_html)
        self.assertIn("角色表现链路已经比较稳", payload["readinessCleanHtml"])
        self.assertIn("这个角色还没有表情条目", payload["emptyExpressionHtml"])


if __name__ == "__main__":
    unittest.main()
