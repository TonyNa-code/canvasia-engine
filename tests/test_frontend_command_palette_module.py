from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "command_palette.js"
STORY_TEMPLATE_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_templates.js"


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
            const projectReleaseReady = tools.buildCommandPaletteCommands({{
              hasProject: true,
              hasSelectedScene: true,
              selectedSceneTitle: "雨夜教室",
              selectedSceneBlockCount: 4,
              selectedBlockType: "dialogue",
              chapterCount: 1,
              sceneCount: 1,
              needsStarterKit: false,
              errorCount: 0,
              hasOneClickPolishReceipt: true,
              oneClickPolishDigest: {{
                canApply: true,
                actionLabel: "一键发布前整理 8 项",
                helperText: "会整理 2 个场景的长文本、演出和音频范围。",
              }},
            }});
            const releaseNoProject = tools.buildReleaseWorkflowCommands({{ hasProject: false }});
            const releaseWithoutReceipt = tools.buildReleaseWorkflowCommands({{
              hasProject: true,
              hasOneClickPolishReceipt: false,
              oneClickPolishDigest: {{ canApply: false, actionLabel: "发布前整理已完成" }},
            }});
            const safetyNoProject = tools.buildProjectSafetyCommands({{ hasProject: false }});
            const safetyNoHistory = tools.buildProjectSafetyCommands({{
              hasProject: true,
              projectHistoryCanUndo: false,
              projectHistoryCanRedo: false,
            }});
            const safetyWithHistory = tools.buildProjectSafetyCommands({{
              hasProject: true,
              projectHistoryCanUndo: true,
              projectHistoryCanRedo: true,
            }});
            const storySearch = tools.filterCommandPaletteCommands(project, "剧情");
            const dialogueSearch = tools.filterCommandPaletteCommands(projectWithScene, "台词");
            const playableSearch = tools.filterCommandPaletteCommands(projectWithScene, "可试玩");
            const affectionSearch = tools.filterCommandPaletteCommands(projectWithScene, "好感度");
            const creditsSearch = tools.filterCommandPaletteCommands(projectWithScene, "片尾");
            const branchMergeSearch = tools.filterCommandPaletteCommands(projectWithScene, "汇合");
            const releaseSearch = tools.filterCommandPaletteCommands(projectReleaseReady, "发布 整理");
            const safetySearch = tools.filterCommandPaletteCommands(projectReleaseReady, "快照");
            const rollbackSearch = tools.filterCommandPaletteCommands(projectReleaseReady, "恢复 版本");
            const exportCommand = project.find((command) => command.id === "export-web");
            const firstChapterCommand = project.find((command) => command.id === "create-first-chapter");
            const disabledDialogueCommand = project.find((command) => command.id === "insert-dialogue");
            const enabledDialogueCommand = projectWithScene.find((command) => command.id === "insert-dialogue");
            const templateCommand = projectWithScene.find((command) => command.id === "template-opening-intro");
            const playableTemplateCommand = projectWithScene.find((command) => command.id === "template-playable-scene");
            const releaseOneClickCommand = projectReleaseReady.find((command) => command.id === "release-one-click-polish");
            const releaseCopyCommand = projectReleaseReady.find((command) => command.id === "release-copy-polish-receipt");
            const releaseExportCommand = projectReleaseReady.find((command) => command.id === "release-export-polish-receipt");
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
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
              noSceneRecommendedIds: tools.getRecommendedCommandIds({{ hasProject: true, hasSelectedScene: false }}),
              releaseNoProjectDisabled: releaseNoProject.map((command) => command.disabled),
              releaseWithoutReceipt: releaseWithoutReceipt.map((command) => [command.id, command.disabled, command.disabledReason]),
              releaseOneClickTitle: releaseOneClickCommand.title,
              releaseOneClickSubtitle: releaseOneClickCommand.subtitle,
              releaseOneClickAction: releaseOneClickCommand.action,
              releaseCopyDisabled: releaseCopyCommand.disabled,
              releaseCopyAction: releaseCopyCommand.action,
              releaseExportDisabled: releaseExportCommand.disabled,
              releaseExportAction: releaseExportCommand.action,
              releaseSearchIds: releaseSearch.map((command) => command.id),
              safetyNoProjectDisabled: safetyNoProject.map((command) => command.disabled),
              safetyNoHistory: safetyNoHistory.map((command) => [command.id, command.disabled, command.disabledReason]),
              safetyWithHistory: safetyWithHistory.map((command) => [command.id, command.disabled, command.action]),
              safetySearchIds: safetySearch.map((command) => command.id),
              rollbackSearchIds: rollbackSearch.map((command) => command.id),
              playableSearchIds: playableSearch.map((command) => command.id),
              affectionSearchIds: affectionSearch.map((command) => command.id),
              creditsSearchIds: creditsSearch.map((command) => command.id),
              branchMergeSearchIds: branchMergeSearch.map((command) => command.id),
              storySearchIds: storySearch.map((command) => command.id),
              clamped: tools.clampCommandPaletteIndex(99, project),
            }}));
            """
        )
        payload = self.run_node(script)

        self.assertIn("buildReleaseWorkflowCommands", payload["keys"])
        self.assertIn("buildProjectSafetyCommands", payload["keys"])
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
        self.assertIn("release-one-click-polish", payload["noSceneRecommendedIds"])
        self.assertTrue(all(payload["releaseNoProjectDisabled"]))
        self.assertIn(["release-copy-polish-receipt", True, "先执行一次一键发布前整理后才有回执"], payload["releaseWithoutReceipt"])
        self.assertEqual(payload["releaseOneClickTitle"], "一键发布前整理 8 项")
        self.assertIn("会整理 2 个场景", payload["releaseOneClickSubtitle"])
        self.assertEqual(payload["releaseOneClickAction"], "run-project-one-click-polish")
        self.assertFalse(payload["releaseCopyDisabled"])
        self.assertEqual(payload["releaseCopyAction"], "copy-project-one-click-polish-receipt-summary")
        self.assertFalse(payload["releaseExportDisabled"])
        self.assertEqual(payload["releaseExportAction"], "export-project-one-click-polish-receipt")
        self.assertIn("release-one-click-polish", payload["releaseSearchIds"])
        self.assertIn("release-export-polish-receipt", payload["releaseSearchIds"])
        self.assertTrue(all(payload["safetyNoProjectDisabled"]))
        self.assertIn(["safety-create-checkpoint", False, ""], payload["safetyNoHistory"])
        self.assertIn(["safety-undo-history", True, "现在没有更早的项目版本可以恢复"], payload["safetyNoHistory"])
        self.assertIn(["safety-restore-previous", True, "现在没有更早的项目版本可以恢复"], payload["safetyNoHistory"])
        self.assertIn(["safety-redo-history", False, "redo-project-history"], payload["safetyWithHistory"])
        self.assertIn(["safety-restore-previous", False, "restore-previous-version"], payload["safetyWithHistory"])
        self.assertIn("safety-create-checkpoint", payload["safetySearchIds"])
        self.assertIn("safety-restore-previous", payload["rollbackSearchIds"])
        self.assertIn("template-playable-scene", payload["playableSearchIds"])
        self.assertIn("template-affection-choice", payload["affectionSearchIds"])
        self.assertIn("template-ending-credits", payload["creditsSearchIds"])
        self.assertIn("template-branch-merge", payload["branchMergeSearchIds"])
        self.assertIn("screen-story", payload["storySearchIds"])
        self.assertGreater(payload["clamped"], 0)

    def test_command_palette_reuses_story_template_recommendations_when_available(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(STORY_TEMPLATE_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorCommandPalette;
            const emptyScene = tools.buildCommandPaletteCommands({{
              hasProject: true,
              hasSelectedScene: true,
              selectedSceneTitle: "空镜",
              selectedSceneBlockCount: 0,
              selectedSceneBlocks: [],
              chapterCount: 1,
              sceneCount: 1,
              needsStarterKit: false,
              errorCount: 0,
            }});
            const dialogueScene = tools.buildCommandPaletteCommands({{
              hasProject: true,
              hasSelectedScene: true,
              selectedSceneTitle: "教室黄昏",
              selectedSceneBlockCount: 4,
              selectedBlockType: "dialogue",
              selectedSceneBlocks: [
                {{ type: "background" }},
                {{ type: "character_show" }},
                {{ type: "dialogue" }},
                {{ type: "dialogue" }},
              ],
              chapterCount: 1,
              sceneCount: 1,
              needsStarterKit: false,
              errorCount: 0,
            }});
            const choiceScene = tools.buildCommandPaletteCommands({{
              hasProject: true,
              hasSelectedScene: true,
              selectedSceneTitle: "分岔口",
              selectedSceneBlockCount: 2,
              selectedBlockType: "choice",
              selectedSceneBlocks: [
                {{ type: "choice" }},
                {{ type: "condition" }},
              ],
              chapterCount: 1,
              sceneCount: 1,
              needsStarterKit: false,
              errorCount: 0,
            }});
            const videoScene = tools.buildCommandPaletteCommands({{
              hasProject: true,
              hasSelectedScene: true,
              selectedSceneTitle: "OP",
              selectedSceneBlockCount: 1,
              selectedBlockType: "video_play",
              selectedSceneBlocks: [
                {{ type: "video_play" }},
              ],
              chapterCount: 1,
              sceneCount: 1,
              needsStarterKit: false,
              errorCount: 0,
            }});
            process.stdout.write(JSON.stringify({{
              directEmptyTemplateIds: tools.getStoryTemplateRecommendationCommandIds({{
                hasSelectedScene: true,
                selectedSceneBlocks: [],
              }}),
              emptySceneRecommendedIds: emptyScene.slice(0, 5).map((command) => command.id),
              dialogueRecommendedIds: dialogueScene.slice(0, 6).map((command) => command.id),
              choiceRecommendedIds: choiceScene.slice(0, 5).map((command) => command.id),
              videoRecommendedIds: videoScene.slice(0, 5).map((command) => command.id),
            }}));
            """
        )
        payload = self.run_node(script)

        self.assertEqual(payload["directEmptyTemplateIds"][:2], ["template-playable-scene", "template-opening-intro"])
        self.assertEqual(payload["emptySceneRecommendedIds"][:3], [
            "template-playable-scene",
            "template-opening-intro",
            "template-daily-conversation",
        ])
        self.assertEqual(payload["dialogueRecommendedIds"][:2], ["insert-dialogue", "insert-choice"])
        self.assertIn("template-branch-choice", payload["dialogueRecommendedIds"])
        self.assertIn("template-affection-choice", payload["dialogueRecommendedIds"])
        self.assertIn("template-branch-merge", payload["choiceRecommendedIds"])
        self.assertIn("template-ending-credits", payload["videoRecommendedIds"])

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
