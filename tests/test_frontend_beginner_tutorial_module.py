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
            const result = {{
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
            }};
            console.log(JSON.stringify(result));
            """
        )
        completed = subprocess.run(["node", "-e", script], text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)

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


if __name__ == "__main__":
    unittest.main()
