from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "beginner_tutorial.js"


class FrontendBeginnerTutorialModuleTests(unittest.TestCase):
    def test_beginner_tutorial_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorBeginnerTutorial;
            const data = {{
              project: {{ title: "测试项目" }},
              scenes: [
                {{ blocks: [{{ type: "background" }}, {{ type: "dialogue", text: "你好" }}] }},
              ],
            }};
            const steps = tools.buildBeginnerTutorialSteps({{
              data,
              starterKitOverview: {{ needsStarterKit: true, missingLabels: ["角色", "BGM"] }},
              previewProgress: true,
              lastExportResult: null,
            }});
            const content = tools.renderBeginnerTutorialContent(steps[0], {{
              escapeHtml: (value) => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
              renderQuickActionButton: (action) => `<button data-action="${{action.action}}">${{action.label}}</button>`,
            }});
            const quickRenderer = (action, emphasized) => `<button data-action="${{action.action}}" data-em="${{emphasized ? "1" : "0"}}">${{action.label}}</button>`;
            const workflow = {{
              nextStep: {{
                step: "第 2 步",
                title: "写第一段 <正文>",
                description: "先写一句 & 试玩",
                actions: [{{ label: "去剧情页", action: "switch-screen" }}],
              }},
              steps: [
                {{
                  step: "第 1 步",
                  title: "创建项目骨架",
                  description: "已有章节",
                  done: true,
                }},
                {{
                  step: "第 2 步",
                  title: "写第一段正文",
                  description: "继续写",
                  done: false,
                  statusLabel: "等待处理",
                  statusTone: "danger",
                }},
              ],
            }};
            const workflowMarkup = tools.renderBeginnerDashboardWorkflow(workflow, {{
              renderQuickActionButton: quickRenderer,
            }});
            const advancedMarkup = tools.renderBeginnerAdvancedToolsPanel({{
              renderQuickActionButton: quickRenderer,
            }});
            const starterKitMarkup = tools.renderStarterKitPanel({{
              needsStarterKit: true,
              missingLabels: ["角色 <A>", "BGM"],
              missingCharacter: true,
              missingBackground: true,
              missingBgm: false,
            }}, {{
              characterName: "女主 <默认>",
              backgroundName: "雨夜 & 教室",
              bgmName: "开场 BGM",
            }}, "story");
            const starterKitHiddenMarkup = tools.renderStarterKitPanel({{ needsStarterKit: false }}, {{}});
            const blankProjectMarkup = tools.renderBlankProjectStarterPanel({{
              chapterName: "第一章 <起点>",
              firstSceneName: "教室 & 黄昏",
            }}, "story");
            const blankStoryMarkup = tools.renderBlankStoryWorkspacePanel();
            const result = {{
              keys: Object.keys(tools).sort(),
              storyContent: tools.hasBeginnerTutorialStoryContent(data),
              noStoryContent: tools.hasBeginnerTutorialStoryContent({{ scenes: [{{ blocks: [{{ type: "background" }}] }}] }}),
              previewProgress: tools.hasBeginnerTutorialPreviewProgress({{
                previewSession: {{ timeline: [1, 2] }},
                previewSaveSlots: [],
              }}, (session) => session),
              stepCount: steps.length,
              firstDone: steps[0].done,
              starterTitle: steps[3].title,
              defaultStep: tools.getBeginnerTutorialDefaultStepIndex(steps),
              clampedHigh: tools.clampBeginnerTutorialStepIndex(99, steps),
              summary: tools.getBeginnerTutorialSummary({{ data, activeProjectTitle: "测试项目" }}),
              listHasButtons: tools.renderBeginnerTutorialStepList(steps, 0, String).includes("beginner-tutorial-step-button"),
              contentHasAction: content.includes('data-action="open-project-center"'),
              workflowStatus: [
                tools.getBeginnerWorkflowStepStatusLabel(workflow.steps[0]),
                tools.getBeginnerWorkflowStepStatusLabel(workflow.steps[1]),
              ],
              workflowTone: [
                tools.getBeginnerWorkflowStepToneClass(workflow.steps[0]),
                tools.getBeginnerWorkflowStepToneClass(workflow.steps[1]),
              ],
              workflowMarkup,
              advancedMarkup,
              starterKitMarkup,
              starterKitHiddenMarkup,
              blankProjectMarkup,
              blankStoryMarkup,
            }};
            console.log(JSON.stringify(result));
            """
        )
        completed = subprocess.run(["node", "-e", script], text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)

        self.assertIn("renderBeginnerDashboardWorkflow", result["keys"])
        self.assertIn("renderBeginnerAdvancedToolsPanel", result["keys"])
        self.assertIn("renderStarterKitPanel", result["keys"])
        self.assertIn("renderBlankProjectStarterPanel", result["keys"])
        self.assertIn("renderBlankStoryWorkspacePanel", result["keys"])
        self.assertTrue(result["storyContent"])
        self.assertFalse(result["noStoryContent"])
        self.assertTrue(result["previewProgress"])
        self.assertEqual(result["stepCount"], 6)
        self.assertTrue(result["firstDone"])
        self.assertIn("角色", result["starterTitle"])
        self.assertEqual(result["defaultStep"], 3)
        self.assertEqual(result["clampedHigh"], 5)
        self.assertIn("当前项目", result["summary"])
        self.assertTrue(result["listHasButtons"])
        self.assertTrue(result["contentHasAction"])
        self.assertEqual(result["workflowStatus"], ["当前已完成", "等待处理"])
        self.assertEqual(result["workflowTone"], ["good-text", "danger-text"])
        self.assertIn("新手开工顺序", result["workflowMarkup"])
        self.assertIn("写第一段 &lt;正文&gt;", result["workflowMarkup"])
        self.assertIn("先写一句 &amp; 试玩", result["workflowMarkup"])
        self.assertIn('data-action="switch-screen"', result["workflowMarkup"])
        self.assertIn('data-em="1"', result["workflowMarkup"])
        self.assertIn("更多高级工具", result["advancedMarkup"])
        self.assertIn('data-action="set-editor-mode"', result["advancedMarkup"])
        self.assertIn("第二步起步骨架", result["starterKitMarkup"])
        self.assertIn("角色 &lt;A&gt;", result["starterKitMarkup"])
        self.assertIn("女主 &lt;默认&gt;", result["starterKitMarkup"])
        self.assertIn("雨夜 &amp; 教室", result["starterKitMarkup"])
        self.assertIn('data-action="create-starter-kit"', result["starterKitMarkup"])
        self.assertEqual(result["starterKitHiddenMarkup"], "")
        self.assertIn("空白项目首次引导", result["blankProjectMarkup"])
        self.assertIn("第一章 &lt;起点&gt;", result["blankProjectMarkup"])
        self.assertIn("教室 &amp; 黄昏", result["blankProjectMarkup"])
        self.assertIn('data-action="create-first-chapter"', result["blankProjectMarkup"])
        self.assertIn('data-screen="assets"', result["blankProjectMarkup"])
        self.assertIn("剧情工作台还没有章节和场景", result["blankStoryMarkup"])
        self.assertIn('data-action="create-first-chapter-custom"', result["blankStoryMarkup"])


if __name__ == "__main__":
    unittest.main()
