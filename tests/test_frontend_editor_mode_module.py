from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "editor_mode.js"
STORY_TEMPLATE_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_templates.js"


class FrontendEditorModeModuleTests(unittest.TestCase):
    def test_editor_mode_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorMode;
            const quickRenderer = (action, primary) =>
              `<button data-action="${{action.action}}" data-primary="${{primary}}" data-template-id="${{action.dataset?.["template-id"] ?? ""}}">${{action.label}}</button>`;
            const playableTemplateSummary = {{
              title: "第一段可试玩",
              blockCount: 10,
              labels: ["切换背景", "播放音乐", "显示角色", "台词 x 3", "选项"],
            }};
            const result = {{
              safeBeginner: tools.getSafeEditorMode("unknown"),
              safeAdvanced: tools.getSafeEditorMode(" Advanced "),
              projectMode: tools.getProjectEditorMode({{ editorMode: "advanced" }}),
              isAdvanced: tools.isAdvancedEditorMode({{ editorMode: "advanced" }}),
              beginnerLabel: tools.getEditorModeLabel("beginner"),
              advancedLabel: tools.getEditorModeLabel("advanced"),
              previewBeginner: tools.getNavScreenLabel("preview", "beginner"),
              assetsAdvanced: tools.getNavScreenLabel("assets", "advanced"),
              unknownScreen: tools.getNavScreenLabel("custom", "advanced"),
              storyDescription: tools.getEditorModeDescription("beginner", "story"),
              inspectionDescription: tools.getEditorModeDescription("advanced", "inspection"),
              storyToolbarHasDialogue: tools.BEGINNER_STORY_TOOLBAR_ACTIONS.has("add-dialogue"),
              storyToolbarHidesCondition: tools.BEGINNER_STORY_TOOLBAR_ACTIONS.has("add-condition"),
              assetToolbarHasPick: tools.BEGINNER_ASSET_TOOLBAR_ACTIONS.has("pick-assets"),
              emptyWorkflow: tools.buildBeginnerStoryWorkflow(null),
              blankWorkflow: tools.buildBeginnerStoryWorkflow({{ id: "scene_1", blocks: [] }}),
              blankWorkflowWithSummary: tools.buildBeginnerStoryWorkflow({{ id: "scene_1", blocks: [] }}, {{
                playableTemplateSummary,
              }}),
              normalizedSummary: tools.normalizeWorkflowTemplateSummary(playableTemplateSummary),
              storyWorkflow: tools.buildBeginnerStoryWorkflow({{
                id: "scene_2",
                blocks: [
                  {{ type: "dialogue" }},
                  {{ type: "narration" }},
                  {{ type: "background" }},
                  {{ type: "music_play" }},
                  {{ type: "choice" }},
                  {{ type: "screen_flash" }},
                ],
              }}),
              partialWorkflow: tools.buildBeginnerStoryWorkflow({{
                id: "scene_3",
                blocks: [
                  {{ type: "dialogue" }},
                  {{ type: "background" }},
                ],
              }}),
              switchMarkup: tools.renderEditorModeSwitchButtons("advanced", {{ compact: true }}),
              guideMarkup: tools.renderEditorModeGuideCard("story", {{ mode: "beginner" }}),
              workflowMarkup: tools.renderBeginnerStoryWorkflow({{ id: "scene_4", blocks: [] }}, {{
                playableTemplateSummary,
                renderQuickActionButton: quickRenderer,
              }}),
              beginnerBannerMarkup: tools.renderStoryEditorModeBanner({{ id: "scene_5", blocks: [] }}, {{
                mode: "beginner",
                hiddenCount: 3,
                playableTemplateSummary,
                renderQuickActionButton: quickRenderer,
              }}),
              advancedBannerMarkup: tools.renderStoryEditorModeBanner({{ id: "scene_6", blocks: [] }}, {{
                mode: "advanced",
                hiddenCount: 3,
                renderQuickActionButton: quickRenderer,
              }}),
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
        self.assertEqual(payload["safeBeginner"], "beginner")
        self.assertEqual(payload["safeAdvanced"], "advanced")
        self.assertEqual(payload["projectMode"], "advanced")
        self.assertTrue(payload["isAdvanced"])
        self.assertEqual(payload["beginnerLabel"], "新手模式")
        self.assertEqual(payload["advancedLabel"], "高级模式")
        self.assertEqual(payload["previewBeginner"], "试玩收尾")
        self.assertEqual(payload["assetsAdvanced"], "管素材")
        self.assertEqual(payload["unknownScreen"], "custom")
        self.assertIn("常用剧情骨架按钮", payload["storyDescription"])
        self.assertIn("集中 QA", payload["inspectionDescription"])
        self.assertTrue(payload["storyToolbarHasDialogue"])
        self.assertFalse(payload["storyToolbarHidesCondition"])
        self.assertTrue(payload["assetToolbarHasPick"])
        self.assertIsNone(payload["emptyWorkflow"])
        self.assertEqual(payload["blankWorkflow"]["nextStep"]["step"], "第一步")
        self.assertEqual(payload["blankWorkflow"]["nextStep"]["actions"][0]["action"], "apply-story-template")
        self.assertEqual(payload["blankWorkflow"]["nextStep"]["actions"][0]["dataset"]["template-id"], "playable_scene")
        self.assertEqual(payload["blankWorkflow"]["nextStep"]["actions"][0]["label"], "生成可试玩段落")
        self.assertEqual(payload["blankWorkflow"]["steps"][0]["done"], False)
        self.assertEqual(payload["blankWorkflowWithSummary"]["nextStep"]["templateSummary"]["title"], "第一段可试玩")
        self.assertEqual(payload["blankWorkflowWithSummary"]["nextStep"]["templateSummary"]["blockCount"], 10)
        self.assertIn("台词 x 3", payload["normalizedSummary"]["labels"])
        self.assertEqual(payload["storyWorkflow"]["steps"], [
            {
                "step": "第一步",
                "title": "写入这一场的基础正文",
                "done": True,
                "description": "这一场已经有 2 张正文卡片了，可以继续往下补氛围和去向。",
                "actions": [
                    {"label": "继续加台词", "action": "add-dialogue"},
                    {"label": "加一张旁白", "action": "add-narration"},
                ],
            },
            {
                "step": "第二步",
                "title": "补齐基础演出氛围",
                "done": True,
                "description": "这一场已经有基础空间感了，人物和音乐至少有一项进来了。",
                "actions": [
                    {"label": "再显一个角色", "action": "add-character-show"},
                    {"label": "补人物亮相", "action": "add-character-show"},
                ],
            },
            {
                "step": "第三步",
                "title": "补齐这一场的去向",
                "done": True,
                "description": "这场已经有下一步去向了，后面就可以开始试玩路线。",
                "actions": [
                    {"label": "加选项分支", "action": "add-choice"},
                    {"label": "直接跳下一场", "action": "add-jump"},
                ],
            },
            {
                "step": "第四步",
                "title": "补充强化演出",
                "done": True,
                "description": "这一场已经有至少一种强化演出，记忆点开始出来了。",
                "actions": [
                    {"label": "加粒子特效", "action": "add-particle-effect"},
                    {"label": "去试玩这场", "action": "preview-scene-from-map", "sceneId": "scene_2"},
                ],
            },
        ])
        self.assertEqual(payload["storyWorkflow"]["nextStep"]["step"], "第四步")
        self.assertEqual(payload["partialWorkflow"]["nextStep"]["step"], "第二步")
        self.assertEqual(payload["partialWorkflow"]["nextStep"]["actions"][0]["action"], "add-character-show")
        self.assertIn('data-editor-mode="advanced"', payload["switchMarkup"])
        self.assertIn("is-active", payload["switchMarkup"])
        self.assertIn("is-compact", payload["switchMarkup"])
        self.assertIn("剧情工具栏分层", payload["guideMarkup"])
        self.assertIn("打开新手教程", payload["guideMarkup"])
        self.assertIn("新手上手顺序", payload["workflowMarkup"])
        self.assertIn('data-action="apply-story-template"', payload["workflowMarkup"])
        self.assertIn('data-template-id="playable_scene"', payload["workflowMarkup"])
        self.assertIn("第一段可试玩 · 将插入 10 张卡片", payload["workflowMarkup"])
        self.assertIn("台词 x 3", payload["workflowMarkup"])
        self.assertIn("已收起 3 个高级按钮", payload["beginnerBannerMarkup"])
        self.assertIn("新手上手顺序", payload["beginnerBannerMarkup"])
        self.assertIn("完整工具栏已展开", payload["advancedBannerMarkup"])
        self.assertNotIn("新手上手顺序", payload["advancedBannerMarkup"])

    def test_editor_mode_workflow_reuses_story_template_recommendations_when_available(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(STORY_TEMPLATE_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorMode;
            const quickRenderer = (action, primary) =>
              `<button data-action="${{action.action}}" data-primary="${{primary}}" data-template-id="${{action.dataset?.["template-id"] ?? ""}}">${{action.label}}</button>`;
            const videoWorkflow = tools.buildBeginnerStoryWorkflow({{
              id: "scene_op",
              blocks: [
                {{ type: "video_play" }},
              ],
            }}, {{
              getBlockLabel: (type) => type === "credits_roll" ? "片尾字幕" : `卡片:${{type}}`,
            }});
            const videoMarkup = tools.renderBeginnerStoryWorkflow({{
              id: "scene_op",
              blocks: [
                {{ type: "video_play" }},
              ],
            }}, {{
              getBlockLabel: (type) => type === "credits_roll" ? "片尾字幕" : `卡片:${{type}}`,
              renderQuickActionButton: quickRenderer,
            }});
            const emptyWorkflow = tools.buildBeginnerStoryWorkflow({{
              id: "scene_empty",
              blocks: [],
            }});
            process.stdout.write(JSON.stringify({{
              videoWorkflow,
              videoMarkup,
              emptyWorkflow,
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
        self.assertEqual(payload["videoWorkflow"]["nextStep"]["step"], "第一步")
        self.assertEqual(payload["videoWorkflow"]["nextStep"]["title"], "按当前内容补下一段演出")
        self.assertEqual(payload["videoWorkflow"]["nextStep"]["actions"][0]["dataset"]["template-id"], "ending_credits")
        self.assertEqual(payload["videoWorkflow"]["nextStep"]["templateSummary"]["title"], "ED 与片尾")
        self.assertIn("片尾字幕", payload["videoWorkflow"]["nextStep"]["templateSummary"]["labels"])
        self.assertIn('data-template-id="ending_credits"', payload["videoMarkup"])
        self.assertIn("ED 与片尾 · 将插入", payload["videoMarkup"])
        self.assertEqual(payload["emptyWorkflow"]["nextStep"]["actions"][0]["dataset"]["template-id"], "playable_scene")


if __name__ == "__main__":
    unittest.main()
