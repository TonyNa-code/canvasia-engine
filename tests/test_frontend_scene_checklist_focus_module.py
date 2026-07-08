from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "scene_checklist_focus.js"


class FrontendSceneChecklistFocusModuleTests(unittest.TestCase):
    def test_scene_checklist_focus_helpers_are_pure_and_predictable(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorSceneChecklistFocus;
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              emptyOptions: tools.getAddBlockOptionsFromDataset({{}}),
              musicOptions: tools.getAddBlockOptionsFromDataset({{ sceneChecklistComplete: " music " }}),
              badOptions: tools.getAddBlockOptionsFromDataset(null),
              shouldComplete: tools.shouldCompleteFocus({{ item: "music" }}, " music "),
              shouldIgnoreMismatch: tools.shouldCompleteFocus({{ item: "voice" }}, "music"),
              shouldIgnoreEmpty: tools.shouldCompleteFocus({{ item: "music" }}, ""),
              feedback: tools.buildCompletionFeedback({{ title: "补 BGM" }}, "播放音乐"),
              fallbackFeedback: tools.buildCompletionFeedback({{ label: "补背景" }}, ""),
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

        self.assertEqual(
            payload["keys"],
            ["buildCompletionFeedback", "getAddBlockOptionsFromDataset", "shouldCompleteFocus"],
        )
        self.assertEqual(payload["emptyOptions"], {"checklistCompleteItem": ""})
        self.assertEqual(payload["musicOptions"], {"checklistCompleteItem": "music"})
        self.assertEqual(payload["badOptions"], {"checklistCompleteItem": ""})
        self.assertTrue(payload["shouldComplete"])
        self.assertFalse(payload["shouldIgnoreMismatch"])
        self.assertFalse(payload["shouldIgnoreEmpty"])
        self.assertEqual(payload["feedback"]["title"], "补 BGM")
        self.assertEqual(payload["feedback"]["toastMessage"], "补 BGM已处理")
        self.assertIn("已新增播放音乐", payload["feedback"]["statusMessage"])
        self.assertIn("可试玩清单会重新计算", payload["feedback"]["statusMessage"])
        self.assertEqual(payload["fallbackFeedback"]["title"], "补背景")
        self.assertIn("已新增剧情卡片", payload["fallbackFeedback"]["statusMessage"])


if __name__ == "__main__":
    unittest.main()
