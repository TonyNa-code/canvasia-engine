from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "command_palette.js"


class FrontendCommandPaletteModuleTests(unittest.TestCase):
    def run_node(self, script: str) -> dict:
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_command_palette_builds_contextual_commands_and_search(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorCommandPalette;
            const noProject = tools.buildCommandPaletteCommands({{ hasProject: false }});
            const project = tools.buildCommandPaletteCommands({{
              hasProject: true,
              chapterCount: 0,
              sceneCount: 0,
              needsStarterKit: true,
              errorCount: 0,
            }});
            const storySearch = tools.filterCommandPaletteCommands(project, "剧情");
            const exportCommand = project.find((command) => command.id === "export-web");
            const firstChapterCommand = project.find((command) => command.id === "create-first-chapter");
            process.stdout.write(JSON.stringify({{
              noProjectStoryDisabled: noProject.find((command) => command.id === "screen-story").disabled,
              noProjectDemoDisabled: noProject.find((command) => command.id === "create-playable-demo").disabled,
              exportDisabled: exportCommand.disabled,
              firstChapterDisabled: firstChapterCommand.disabled,
              firstChapterAction: firstChapterCommand.action,
              storySearchIds: storySearch.map((command) => command.id),
              clamped: tools.clampCommandPaletteIndex(99, project),
            }}));
            """
        )
        payload = self.run_node(script)

        self.assertTrue(payload["noProjectStoryDisabled"])
        self.assertFalse(payload["noProjectDemoDisabled"])
        self.assertFalse(payload["exportDisabled"])
        self.assertFalse(payload["firstChapterDisabled"])
        self.assertEqual(payload["firstChapterAction"], "create-first-chapter")
        self.assertIn("screen-story", payload["storySearchIds"])
        self.assertGreater(payload["clamped"], 0)

    def test_command_palette_renderer_marks_selected_and_disabled_commands(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorCommandPalette;
            const html = tools.renderCommandPaletteList([
              {{ id: "a", title: "打开 <剧情>", section: "导航", subtitle: "去写", action: "switch-screen" }},
              {{ id: "b", title: "导出", section: "发布", subtitle: "先修错误", disabled: true, disabledReason: "不可用" }},
            ], 1, {{
              escapeHtml(value) {{
                return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
              }}
            }});
            process.stdout.write(JSON.stringify({{ html }}));
            """
        )
        html = self.run_node(script)["html"]

        self.assertIn('data-command-id="a"', html)
        self.assertIn("打开 &lt;剧情&gt;", html)
        self.assertIn("is-selected", html)
        self.assertIn("is-disabled", html)
        self.assertIn('aria-disabled="true"', html)


if __name__ == "__main__":
    unittest.main()
