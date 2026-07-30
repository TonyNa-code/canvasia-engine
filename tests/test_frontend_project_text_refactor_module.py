from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_text_refactor.js"


class FrontendProjectTextRefactorModuleTests(unittest.TestCase):
    def test_text_refactor_state_payload_validation_and_report_rendering(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectTextRefactor;
            const state = tools.createProjectTextRefactorState({{
              findText: "旧称",
              replaceText: "<新称>",
              scopes: ["dialogue", "choice", "unknown"],
              caseSensitive: false,
              includeTranslations: true,
            }});
            state.report = {{
              totalReplacements: 3,
              changedChapterCount: 1,
              changedSceneCount: 1,
              matches: [{{
                fieldLabel: "角色台词",
                chapterName: "第一章",
                sceneName: "教室",
                sceneId: "scene_1",
                blockId: "line_1",
                before: "旧称出现了",
                after: "<新称>出现了",
              }}],
              truncatedMatchCount: 2,
            }};
            const payload = tools.buildProjectTextRefactorPayload(state);
            const panel = tools.renderProjectTextRefactorPanel(state);
            const report = tools.renderProjectTextRefactorReport(state.report);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              payload,
              emptyError: tools.getProjectTextRefactorValidationError(tools.createProjectTextRefactorState()),
              sameError: tools.getProjectTextRefactorValidationError({{
                findText: "Hero",
                replaceText: "hero",
                scopes: ["dialogue"],
                caseSensitive: false,
              }}),
              panel,
              report,
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
        self.assertIn("renderProjectTextRefactorPanel", payload["keys"])
        self.assertEqual(payload["payload"]["scopes"], ["dialogue", "choice"])
        self.assertFalse(payload["payload"]["caseSensitive"])
        self.assertTrue(payload["payload"]["includeTranslations"])
        self.assertIn("先填写", payload["emptyError"])
        self.assertIn("相同", payload["sameError"])
        self.assertIn("剧情重构台", payload["panel"])
        self.assertIn("确认替换 3 处", payload["panel"])
        self.assertIn("&lt;新称&gt;", payload["report"])
        self.assertNotIn("<新称>", payload["report"])
        self.assertIn("另外还有 2 条", payload["report"])


if __name__ == "__main__":
    unittest.main()
