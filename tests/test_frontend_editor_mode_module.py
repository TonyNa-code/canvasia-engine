from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "editor_mode.js"


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


if __name__ == "__main__":
    unittest.main()
