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
            const projectWithScene = tools.buildCommandPaletteCommands({{
              hasProject: true,
              hasSelectedScene: true,
              selectedSceneTitle: "雨夜教室",
              selectedSceneBlockCount: 0,
              chapterCount: 1,
              sceneCount: 1,
              needsStarterKit: false,
              errorCount: 0,
            }});
            const projectAfterDialogue = tools.buildCommandPaletteCommands({{
              hasProject: true,
              hasSelectedScene: true,
              selectedSceneTitle: "雨夜教室",
              selectedSceneBlockCount: 4,
              selectedBlockType: "dialogue",
              recentCommandIds: ["insert-video", "screen-preview", "insert-choice", "bad id"],
              chapterCount: 1,
              sceneCount: 1,
              needsStarterKit: false,
              errorCount: 0,
            }});
            const storySearch = tools.filterCommandPaletteCommands(project, "剧情");
            const dialogueSearch = tools.filterCommandPaletteCommands(projectWithScene, "台词");
            const playableSearch = tools.filterCommandPaletteCommands(projectWithScene, "可试玩");
            const exportCommand = project.find((command) => command.id === "export-web");
            const firstChapterCommand = project.find((command) => command.id === "create-first-chapter");
            const disabledDialogueCommand = project.find((command) => command.id === "insert-dialogue");
            const enabledDialogueCommand = projectWithScene.find((command) => command.id === "insert-dialogue");
            const templateCommand = projectWithScene.find((command) => command.id === "template-opening-intro");
            const playableTemplateCommand = projectWithScene.find((command) => command.id === "template-playable-scene");
            process.stdout.write(JSON.stringify({{
              noProjectStoryDisabled: noProject.find((command) => command.id === "screen-story").disabled,
              noProjectDemoDisabled: noProject.find((command) => command.id === "create-playable-demo").disabled,
              exportDisabled: exportCommand.disabled,
              firstChapterDisabled: firstChapterCommand.disabled,
              firstChapterAction: firstChapterCommand.action,
              disabledDialogueReason: disabledDialogueCommand.disabledReason,
              enabledDialogueDisabled: enabledDialogueCommand.disabled,
              enabledDialogueSubtitle: enabledDialogueCommand.subtitle,
              enabledDialogueAction: enabledDialogueCommand.action,
              dialogueSearchIds: dialogueSearch.map((command) => command.id),
              templateAction: templateCommand.action,
              templateId: templateCommand.dataset["template-id"],
              playableTemplateAction: playableTemplateCommand.action,
              playableTemplateId: playableTemplateCommand.dataset["template-id"],
              emptySceneRecommendedIds: projectWithScene.slice(0, 4).map((command) => command.id),
              emptySceneRecommendedSections: projectWithScene.slice(0, 2).map((command) => command.section),
              dialogueRecommendedIds: projectAfterDialogue.slice(0, 4).map((command) => command.id),
              dialogueRecentIds: projectAfterDialogue.slice(4, 6).map((command) => command.id),
              dialogueRecentSections: projectAfterDialogue.slice(4, 6).map((command) => command.section),
              directRecommendedIds: tools.getRecommendedCommandIds({{ hasProject: true, hasSelectedScene: true, selectedBlockType: "dialogue", selectedSceneBlockCount: 2 }}),
              playableSearchIds: playableSearch.map((command) => command.id),
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
        self.assertIn("先创建或选择一个场景", payload["disabledDialogueReason"])
        self.assertFalse(payload["enabledDialogueDisabled"])
        self.assertEqual(payload["enabledDialogueAction"], "add-dialogue")
        self.assertIn("雨夜教室", payload["enabledDialogueSubtitle"])
        self.assertIn("insert-dialogue", payload["dialogueSearchIds"])
        self.assertEqual(payload["templateAction"], "apply-story-template")
        self.assertEqual(payload["templateId"], "opening_intro")
        self.assertEqual(payload["playableTemplateAction"], "apply-story-template")
        self.assertEqual(payload["playableTemplateId"], "playable_scene")
        self.assertEqual(payload["emptySceneRecommendedIds"][:3], ["template-playable-scene", "template-opening-intro", "insert-background"])
        self.assertEqual(payload["emptySceneRecommendedSections"], ["推荐", "推荐"])
        self.assertEqual(payload["dialogueRecommendedIds"][:3], ["insert-dialogue", "insert-choice", "template-emotion-burst"])
        self.assertEqual(payload["dialogueRecentIds"], ["insert-video", "screen-preview"])
        self.assertEqual(payload["dialogueRecentSections"], ["最近", "最近"])
        self.assertEqual(payload["directRecommendedIds"][:2], ["insert-dialogue", "insert-choice"])
        self.assertIn("template-playable-scene", payload["playableSearchIds"])
        self.assertIn("screen-story", payload["storySearchIds"])
        self.assertGreater(payload["clamped"], 0)

    def test_command_palette_recent_ids_are_sanitized_merged_and_persisted(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorCommandPalette;
            const storage = {{
              value: "",
              getItem(key) {{ return this.value; }},
              setItem(key, value) {{ this.key = key; this.value = value; }},
            }};
            const key = tools.getCommandPaletteRecentStorageKey("Project Alpha!");
            const sanitized = tools.sanitizeCommandPaletteRecentIds(
              ["insert-dialogue", "bad id", "insert-dialogue", "screen-preview", "unknown"],
              {{ availableIds: ["insert-dialogue", "screen-preview"], limit: 6 }}
            );
            const merged = tools.mergeCommandPaletteRecentId(
              ["insert-dialogue", "screen-preview"],
              "insert-video",
              {{ limit: 3 }}
            );
            const moved = tools.mergeCommandPaletteRecentId(
              merged,
              "insert-dialogue",
              {{ limit: 3 }}
            );
            const persisted = tools.persistStoredCommandPaletteRecentIds(storage, key, ["insert-dialogue", "bad id", "screen-preview"], {{
              availableIds: ["insert-dialogue", "screen-preview"],
              limit: 3,
            }});
            const stored = JSON.parse(storage.value || "[]");
            const loaded = tools.loadStoredCommandPaletteRecentIds(storage, key, {{ limit: 3 }});
            storage.value = "{{bad json";
            const broken = tools.loadStoredCommandPaletteRecentIds(storage, key, {{ limit: 3 }});
            process.stdout.write(JSON.stringify({{ key, sanitized, merged, moved, persisted, stored, loaded, broken }}));
            """
        )
        payload = self.run_node(script)

        self.assertEqual(payload["key"], "canvasia-engine:editor-command-recent:project-alpha-")
        self.assertEqual(payload["sanitized"], ["insert-dialogue", "screen-preview"])
        self.assertEqual(payload["merged"], ["insert-video", "insert-dialogue", "screen-preview"])
        self.assertEqual(payload["moved"], ["insert-dialogue", "insert-video", "screen-preview"])
        self.assertTrue(payload["persisted"])
        self.assertEqual(payload["stored"], ["insert-dialogue", "screen-preview"])
        self.assertEqual(payload["loaded"], ["insert-dialogue", "screen-preview"])
        self.assertEqual(payload["broken"], [])

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
              {{ id: "a", title: "打开 <剧情>", section: "推荐", originalSection: "导航", subtitle: "去写", action: "switch-screen", recommended: true }},
              {{ id: "c", title: "插入台词", section: "最近", originalSection: "插卡", subtitle: "继续写", action: "add-dialogue", recent: true }},
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
        self.assertIn("推荐 · 导航", html)
        self.assertIn("is-recommended", html)
        self.assertIn("最近 · 插卡", html)
        self.assertIn("is-recent", html)
        self.assertIn("is-selected", html)
        self.assertIn("is-disabled", html)
        self.assertIn('aria-disabled="true"', html)


if __name__ == "__main__":
    unittest.main()
