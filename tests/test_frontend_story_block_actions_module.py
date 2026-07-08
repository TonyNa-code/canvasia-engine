from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_actions.js"


class FrontendStoryBlockActionsModuleTests(unittest.TestCase):
    def test_story_block_action_map_covers_editor_add_buttons(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStoryBlockActions;
            const dialogueConfig = tools.getAddBlockActionConfig("add-dialogue");
            const missingConfig = tools.getAddBlockActionConfig("add-missing");
            const variableAddConfig = tools.getAddBlockActionConfig("add-variable-add");
            const mutableConfig = tools.getAddBlockActionConfig("add-variable-add");
            mutableConfig.variableRequirement.reason = "mutated";
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              groupLabels: tools.GROUP_LABELS,
              entries: tools.getAddBlockActionEntries(),
              dialogueConfig,
              missingConfig,
              variableAddConfig,
              stableVariableAddConfig: tools.getAddBlockActionConfig("add-variable-add"),
              dialogueTitle: tools.buildButtonTitle(dialogueConfig),
              flowLabel: tools.getGroupLabel("flow"),
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
        entries = payload["entries"]
        action_to_block = {entry["action"]: entry["blockType"] for entry in entries}

        self.assertEqual(
            payload["keys"],
            [
                "ADD_BLOCK_ACTIONS",
                "GROUP_LABELS",
                "buildButtonTitle",
                "getAddBlockActionConfig",
                "getAddBlockActionEntries",
                "getGroupLabel",
            ],
        )
        self.assertEqual(payload["groupLabels"]["story"], "剧情文本")
        self.assertEqual(payload["dialogueConfig"]["blockType"], "dialogue")
        self.assertEqual(payload["dialogueConfig"]["label"], "台词")
        self.assertEqual(payload["dialogueConfig"]["group"], "story")
        self.assertEqual(payload["dialogueConfig"]["groupLabel"], "剧情文本")
        self.assertIn("角色对白", payload["dialogueConfig"]["description"])
        self.assertIsNone(payload["dialogueConfig"]["variableRequirement"])
        self.assertIsNone(payload["missingConfig"])
        self.assertEqual(action_to_block["add-dialogue"], "dialogue")
        self.assertEqual(action_to_block["add-background"], "background")
        self.assertEqual(action_to_block["add-music-play"], "music_play")
        self.assertEqual(action_to_block["add-camera-zoom"], "camera_zoom")
        self.assertEqual(action_to_block["add-variable-set"], "variable_set")
        self.assertEqual(action_to_block["add-variable-add"], "variable_add")
        self.assertEqual(action_to_block["add-condition"], "condition")
        self.assertEqual(len(entries), 24)
        self.assertTrue(payload["variableAddConfig"]["variableRequirement"]["requireNumber"])
        self.assertEqual(payload["variableAddConfig"]["groupLabel"], "路线与逻辑")
        self.assertIn("数字变量变化卡片", payload["variableAddConfig"]["variableRequirement"]["reason"])
        self.assertIn("数字变量变化卡片", payload["stableVariableAddConfig"]["variableRequirement"]["reason"])
        self.assertIn("台词", payload["dialogueTitle"])
        self.assertIn("分类：剧情文本", payload["dialogueTitle"])
        self.assertEqual(payload["flowLabel"], "路线与逻辑")


if __name__ == "__main__":
    unittest.main()
