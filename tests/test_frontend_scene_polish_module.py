from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CATALOG_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_catalog.js"
READABILITY_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "script_readability.js"
PACING_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "scene_pacing_advisor.js"
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "scene_polish.js"


class FrontendScenePolishModuleTests(unittest.TestCase):
    def test_scene_polish_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorScenePolish;
            const scene = {{
              id: "scene_a",
              blocks: [
                {{ id: "line_1", type: "dialogue", text: "你好" }},
                {{ id: "narration_1", type: "narration", text: "风吹过走廊", textSpeed: "slow" }},
                {{ id: "bg_1", type: "background", assetId: "bg_room" }},
                {{ id: "show_1", type: "character_show", characterId: "hero", transition: "slide", transitionDurationMs: 0 }},
                {{ id: "hide_1", type: "character_hide", characterId: "hero", transition: "none", transitionDurationMs: 0 }},
                {{ id: "music_1", type: "music_play", assetId: "bgm", fadeInMs: 0, fadeOutMs: undefined, volume: 0 }},
                {{ id: "stop_1", type: "music_stop", fadeOutMs: 0 }},
                {{ id: "sfx_1", type: "sfx_play", assetId: "bell" }},
              ],
            }};
            const plan = tools.buildScenePresentationPolishPlan(scene);
            const cleanScene = {{ id: "clean", blocks: [
              {{ id: "line_ok", type: "dialogue", text: "短句", textSpeed: "fast" }},
              {{ id: "bg_ok", type: "background", transition: "crossfade", transitionDurationMs: 800 }},
              {{ id: "music_ok", type: "music_play", fadeInMs: 700, fadeOutMs: 900, volume: 65, loop: false, endMode: "after_block" }},
            ] }};
            const cleanPlan = tools.buildScenePresentationPolishPlan(cleanScene);
            const digest = tools.getScenePresentationPolishDigest(scene, {{ tagLimit: 3 }});
            const cleanDigest = tools.getScenePresentationPolishDigest(cleanScene);
            const projectData = {{
              chapters: [
                {{ chapterId: "ch1", name: "第一章", sceneOrder: ["clean", "scene_a"] }},
                {{ chapterId: "ch2", name: "第二章", scenes: [
                  {{ id: "scene_b", name: "雨夜", blocks: [
                    {{ id: "bg_b", type: "background", assetId: "bg_rain", transitionDurationMs: 0 }},
                    {{ id: "music_b", type: "music_play", assetId: "bgm_rain", fadeInMs: 0, fadeOutMs: 0 }},
                  ] }},
                ] }},
              ],
              scenes: [
                scene,
                cleanScene,
                {{ id: "scene_orphan", name: "额外场景", blocks: [
                  {{ id: "line_orphan", type: "narration", text: "补完后单独检查" }},
                ] }},
              ],
            }};
            const projectPlan = tools.buildProjectPresentationPolishPlan(projectData);
            const projectDigest = tools.getProjectPresentationPolishDigest(projectData, {{ sceneNameLimit: 2 }});
            process.stdout.write(JSON.stringify({{
              defaultTransition: tools.DEFAULTS.transition,
              changed: plan.changed,
              changedBlockCount: plan.changedBlockCount,
              changedFieldCount: plan.changedFieldCount,
              firstChangedBlockId: plan.firstChangedBlockId,
              firstChangedIndex: plan.firstChangedIndex,
              summary: plan.summary,
              blocks: plan.scene.blocks,
              operationLabels: plan.operations.flatMap((operation) => operation.fields.map((field) => field.label)),
              cleanChanged: cleanPlan.changed,
              cleanSummary: cleanPlan.summary,
              digest: {{
                canApply: digest.canApply,
                actionLabel: digest.actionLabel,
                badgeLabel: digest.badgeLabel,
                helperText: digest.helperText,
                tags: digest.tags,
              }},
              cleanDigest: {{
                canApply: cleanDigest.canApply,
                actionLabel: cleanDigest.actionLabel,
                badgeLabel: cleanDigest.badgeLabel,
                helperText: cleanDigest.helperText,
                tags: cleanDigest.tags,
              }},
              projectSceneIds: tools.getProjectSceneList(projectData).map((item) => item.id),
              projectPlan: {{
                changed: projectPlan.changed,
                changedSceneCount: projectPlan.changedSceneCount,
                changedBlockCount: projectPlan.changedBlockCount,
                changedFieldCount: projectPlan.changedFieldCount,
                firstChangedSceneId: projectPlan.firstChangedSceneId,
                firstChangedBlockId: projectPlan.firstChangedBlockId,
                summary: projectPlan.summary,
                sceneNames: projectPlan.scenePlans.map((item) => item.sceneName),
              }},
              projectDigest: {{
                canApply: projectDigest.canApply,
                actionLabel: projectDigest.actionLabel,
                badgeLabel: projectDigest.badgeLabel,
                helperText: projectDigest.helperText,
              }},
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
        self.assertEqual(payload["defaultTransition"], "fade")
        self.assertTrue(payload["changed"])
        self.assertGreaterEqual(payload["changedBlockCount"], 6)
        self.assertGreaterEqual(payload["changedFieldCount"], 9)
        self.assertEqual(payload["firstChangedBlockId"], "line_1")
        self.assertEqual(payload["firstChangedIndex"], 0)
        self.assertIn("已润色", payload["summary"])
        self.assertEqual(payload["blocks"][0]["textSpeed"], "normal")
        self.assertEqual(payload["blocks"][1]["textSpeed"], "slow")
        self.assertEqual(payload["blocks"][2]["transition"], "fade")
        self.assertEqual(payload["blocks"][2]["transitionDurationMs"], 700)
        self.assertEqual(payload["blocks"][3]["transition"], "slide")
        self.assertEqual(payload["blocks"][3]["transitionDurationMs"], 620)
        self.assertEqual(payload["blocks"][4]["transition"], "none")
        self.assertEqual(payload["blocks"][4].get("transitionDurationMs"), 0)
        self.assertEqual(payload["blocks"][5]["fadeInMs"], 900)
        self.assertEqual(payload["blocks"][5]["fadeOutMs"], 900)
        self.assertEqual(payload["blocks"][5]["volume"], 88)
        self.assertTrue(payload["blocks"][5]["loop"])
        self.assertEqual(payload["blocks"][5]["endMode"], "until_next_music")
        self.assertEqual(payload["blocks"][6]["fadeOutMs"], 700)
        self.assertEqual(payload["blocks"][7]["volume"], 92)
        self.assertIn("补默认转场", payload["operationLabels"])
        self.assertIn("补 BGM 淡入", payload["operationLabels"])
        self.assertFalse(payload["cleanChanged"])
        self.assertEqual(payload["cleanSummary"], "本场基础演出参数已经比较完整")
        self.assertTrue(payload["digest"]["canApply"])
        self.assertIn("润色", payload["digest"]["actionLabel"])
        self.assertIn("张卡片可润色", payload["digest"]["badgeLabel"])
        self.assertIn("会补齐", payload["digest"]["helperText"])
        self.assertLessEqual(len(payload["digest"]["tags"]), 3)
        self.assertIn("补文字速度", payload["digest"]["tags"])
        self.assertFalse(payload["cleanDigest"]["canApply"])
        self.assertEqual(payload["cleanDigest"]["actionLabel"], "演出参数已完整")
        self.assertEqual(payload["cleanDigest"]["tags"], ["基础演出已完整"])
        self.assertEqual(payload["projectSceneIds"], ["clean", "scene_a", "scene_b", "scene_orphan"])
        self.assertTrue(payload["projectPlan"]["changed"])
        self.assertEqual(payload["projectPlan"]["changedSceneCount"], 3)
        self.assertGreaterEqual(payload["projectPlan"]["changedBlockCount"], 4)
        self.assertGreaterEqual(payload["projectPlan"]["changedFieldCount"], 12)
        self.assertEqual(payload["projectPlan"]["firstChangedSceneId"], "scene_a")
        self.assertEqual(payload["projectPlan"]["firstChangedBlockId"], "line_1")
        self.assertIn("已润色 3 个场景", payload["projectPlan"]["summary"])
        self.assertEqual(payload["projectPlan"]["sceneNames"], ["scene_a", "雨夜", "额外场景"])
        self.assertTrue(payload["projectDigest"]["canApply"])
        self.assertIn("润色全项目", payload["projectDigest"]["actionLabel"])
        self.assertIn("3 个场景可润色", payload["projectDigest"]["badgeLabel"])
        self.assertIn("会处理", payload["projectDigest"]["helperText"])

    def test_scene_polish_builds_director_brief_from_pacing_advisor(self) -> None:
        long_scene_text = "这里已经连续读了很久，但画面还是没有变化。" * 8
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(CATALOG_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(READABILITY_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(PACING_MODULE_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorScenePolish;
            const roughScene = {{
              id: "rough",
              name: "长走廊独白",
              blocks: [
                {{ id: "line_1", type: "dialogue", text: {json.dumps(long_scene_text)} }},
                {{ id: "line_2", type: "dialogue", text: "第二句。" }},
                {{ id: "line_3", type: "dialogue", text: "第三句。" }},
                {{ id: "line_4", type: "narration", text: "第四句。" }},
                {{ id: "line_5", type: "dialogue", text: "第五句。" }},
                {{ id: "line_6", type: "dialogue", text: "第六句。" }},
                {{ id: "show_1", type: "character_show", characterId: "hero", transition: "none" }},
              ],
            }};
            const readyScene = {{
              id: "ready",
              name: "黄昏教室",
              blocks: [
                {{ id: "bg", type: "background", assetId: "bg", transition: "fade", transitionDurationMs: 700 }},
                {{ id: "music", type: "music_play", assetId: "bgm", fadeInMs: 900, fadeOutMs: 900, volume: 80, loop: true, endMode: "until_next_music" }},
                {{ id: "line", type: "dialogue", text: "今天也辛苦了。", textSpeed: "normal", voiceAssetId: "voice_1" }},
                {{ id: "wait", type: "wait", durationSeconds: 0.4 }},
                {{ id: "fade", type: "screen_fade", action: "fade_out" }},
              ],
            }};
            const digest = tools.getScenePresentationPolishDigest(roughScene, {{ tagLimit: 8 }});
            const brief = tools.buildSceneDirectorPolishBrief(roughScene, digest.plan, {{ tagLimit: 8 }});
            const readyDigest = tools.getScenePresentationPolishDigest(readyScene, {{ tagLimit: 5 }});
            const projectDigest = tools.getProjectPresentationPolishDigest({{ scenes: [roughScene, readyScene] }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              digest,
              brief: {{
                changed: brief.changed,
                priority: brief.priority,
                tags: brief.tags,
                helperText: brief.helperText,
                pacingIssueCount: brief.pacingIssueCount,
                pacingScore: brief.pacingScore,
                pacingGradeLabel: brief.pacingGradeLabel,
              }},
              readyDigest,
              projectDigest: {{
                helperText: projectDigest.helperText,
                pacing: projectDigest.pacing,
              }},
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
        self.assertIn("buildSceneDirectorPolishBrief", payload["keys"])
        self.assertTrue(payload["digest"]["canApply"])
        self.assertIn("节奏体检", payload["digest"]["helperText"])
        self.assertIn(payload["digest"]["priority"], ["danger", "warn"])
        self.assertGreaterEqual(payload["digest"]["pacingIssueCount"], 3)
        self.assertLess(payload["digest"]["pacingScore"], 72)
        self.assertIn("补文字速度", payload["digest"]["tags"])
        self.assertIn("补背景", payload["digest"]["tags"])
        self.assertIn("补 BGM 范围", payload["digest"]["tags"])
        self.assertTrue(payload["brief"]["changed"])
        self.assertIn("节奏体检", payload["brief"]["helperText"])
        self.assertGreaterEqual(payload["brief"]["pacingIssueCount"], 3)
        self.assertIn(payload["brief"]["priority"], ["danger", "warn"])
        self.assertFalse(payload["readyDigest"]["canApply"])
        self.assertEqual(payload["readyDigest"]["pacingIssueCount"], 0)
        self.assertEqual(payload["readyDigest"]["priority"], "soft")
        self.assertEqual(payload["projectDigest"]["pacing"]["sceneCount"], 2)
        self.assertGreaterEqual(payload["projectDigest"]["pacing"]["roughSceneCount"], 1)


if __name__ == "__main__":
    unittest.main()
