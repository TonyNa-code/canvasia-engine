from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_template_panel.js"


class FrontendStoryTemplatePanelModuleTests(unittest.TestCase):
    def test_story_template_panel_renders_actionable_template_cards_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStoryTemplatePanel;
            const recommendedLimits = [];
            const storyTemplateTools = {{
              getStoryTemplateRecommendedPanelItems(scene, options) {{
                recommendedLimits.push(options.limit);
                return scene?.id === "scene_1"
                  ? [
                      {{
                        templateId: "playable_scene",
                        isRecommended: true,
                        badgeLabel: "最适合现在",
                        recommendationReason: "当前场景还缺可试玩骨架",
                        tone: "hero",
                      }},
                    ]
                  : [];
              }},
              getStoryTemplatePanelItems() {{
                return [{{ templateId: "fallback_scene", description: "保底模板" }}];
              }},
              getStoryTemplatePreset(templateId) {{
                return templateId === "playable_scene" ? {{ title: "Playable <Scene>" }} : null;
              }},
              getStoryTemplateSummary(templateId, options) {{
                const labels = ["台词 x 2", "选项", options.getBlockLabel("music_play")];
                return {{ templateId, title: "Playable <Scene>", blockCount: 4, labels }};
              }},
              getStoryTemplateVariableRequirement() {{
                return {{ requiresAny: true, requiresNumber: true }};
              }},
            }};
            const items = tools.getStoryTemplatePanelItems({{ id: "scene_1" }}, {{
              storyTemplateTools,
              fallbackTemplateIds: ["fallback_scene"],
              limit: 7,
            }});
            const fallbackItems = tools.getStoryTemplatePanelItems(null, {{
              storyTemplateTools: {{}},
              fallbackTemplateIds: ["fallback_scene"],
            }});
            const description = tools.getStoryTemplateButtonDescription(
              {{ recommendationReason: "适合补第一段" }},
              {{ labels: ["台词", "选项"] }}
            );
            const defaultDescription = tools.getStoryTemplateButtonDescription({{}}, {{ labels: ["台词", "选项"] }});
            const noLabelPlan = tools.buildStoryTemplateButtonPlan({{ blockCount: 0, labels: [] }}, {{ requiresAny: false }});
            const html = tools.renderStoryTemplateButton(items[0], {{
              storyTemplateTools,
              getBlockLabel(type) {{
                return type === "music_play" ? "播放 BGM" : type;
              }},
            }});
            const missingHtml = tools.renderStoryTemplateButton({{ templateId: "missing" }}, {{ storyTemplateTools }});
            const gridHtml = tools.renderStoryTemplateGrid({{ id: "scene_1" }}, {{
              storyTemplateTools,
              getBlockLabel(type) {{
                return type === "music_play" ? "播放 BGM" : type;
              }},
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              recommendedLimits,
              items,
              fallbackItems,
              description,
              defaultDescription,
              noLabelPlan,
              html,
              missingHtml,
              gridHtml,
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

        self.assertIn("renderStoryTemplateButton", payload["keys"])
        self.assertIn("buildStoryTemplateButtonPlan", payload["keys"])
        self.assertIn(7, payload["recommendedLimits"])
        self.assertIn(4, payload["recommendedLimits"])
        self.assertEqual(payload["items"][0]["templateId"], "playable_scene")
        self.assertEqual(payload["fallbackItems"][0]["templateId"], "fallback_scene")
        self.assertEqual(payload["description"], "推荐：适合补第一段")
        self.assertEqual(payload["defaultDescription"], "台词 + 选项")
        self.assertEqual(payload["noLabelPlan"]["summaryText"], "预计插入 0 张剧情卡片")
        self.assertIn('data-action="apply-story-template"', html)
        self.assertIn('data-template-id="playable_scene"', html)
        self.assertIn("Playable &lt;Scene&gt;", html)
        self.assertIn("story-template-recommendation-badge", html)
        self.assertIn("story-template-button-plan", html)
        self.assertIn("预计插入 4 张：台词 x 2 / 选项 / 播放 BGM", html)
        self.assertIn("需要数值变量", html)
        self.assertIn("story-template-button-meta", html)
        self.assertEqual(payload["missingHtml"], "")
        self.assertIn("story-template-button", payload["gridHtml"])


if __name__ == "__main__":
    unittest.main()
