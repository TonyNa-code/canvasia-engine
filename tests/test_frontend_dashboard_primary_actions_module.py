from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "dashboard_primary_actions.js"


class FrontendDashboardPrimaryActionsModuleTests(unittest.TestCase):
    def test_dashboard_primary_actions_build_blank_and_loaded_project_buttons_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorDashboardPrimaryActions;
            const blankActions = tools.buildDashboardPrimaryActionModel({{
              isBlankProject: true,
              chapterCreateInFlight: true,
            }});
            const loadedActions = tools.buildDashboardPrimaryActionModel({{
              hasOneClickPolishReceipt: true,
              oneClickPolishDigest: {{
                canApply: false,
                actionLabel: "没有可整理项",
                helperText: "全部已经可发布",
              }},
              projectPolishDigest: {{ canApply: true, actionLabel: "润色演出 <安全>" }},
              projectReadableDigest: {{ canApply: true, actionLabel: "整理长文本" }},
            }});
            const blankHtml = tools.renderDashboardPrimaryActions({{
              isBlankProject: true,
              chapterCreateInFlight: true,
            }});
            const customButton = tools.renderDashboardPrimaryActionButton({{
              label: "打开 <预览>",
              action: "switch-screen",
              screen: "preview",
              dataset: {{ blockId: "line_1", stepIndex: "2" }},
              title: "A&B",
              primary: true,
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              blankActions,
              loadedActions,
              blankHtml,
              customButton,
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
        blank_actions = payload["blankActions"]
        loaded_actions = payload["loadedActions"]

        self.assertIn("renderDashboardPrimaryActions", payload["keys"])
        self.assertEqual(blank_actions[0]["action"], "create-first-chapter")
        self.assertTrue(blank_actions[0]["primary"])
        self.assertTrue(blank_actions[0]["disabled"])
        self.assertTrue(blank_actions[0]["busy"])
        self.assertEqual(blank_actions[2]["dataset"]["stepIndex"], "1")
        self.assertEqual(loaded_actions[0]["screen"], "story")
        self.assertEqual(loaded_actions[1]["label"], "没有可整理项")
        self.assertTrue(loaded_actions[1]["disabled"])
        self.assertTrue(any(action["action"] == "copy-project-one-click-polish-receipt-summary" for action in loaded_actions))
        self.assertTrue(any(action["action"] == "export-project-one-click-polish-receipt" for action in loaded_actions))
        self.assertIn('aria-busy="true"', payload["blankHtml"])
        self.assertIn('data-step-index="1"', payload["blankHtml"])
        self.assertIn("打开 &lt;预览&gt;", payload["customButton"])
        self.assertIn('data-screen="preview"', payload["customButton"])
        self.assertIn('data-block-id="line_1"', payload["customButton"])
        self.assertIn('title="A&amp;B"', payload["customButton"])


if __name__ == "__main__":
    unittest.main()
