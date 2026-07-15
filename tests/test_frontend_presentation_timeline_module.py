from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "presentation_timeline.js"


class FrontendPresentationTimelineModuleTests(unittest.TestCase):
    def test_stage_image_beats_validate_assets_and_duration(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const timeline = context.window.CanvasiaEditorPresentationTimeline.buildPresentationTimeline({{
              assetList: [{{ id: "letter", type: "cg", name: "信件", fileExists: true }}],
              scenes: [{{ id: "scene", name: "Scene", blocks: [
                {{ id: "show", type: "stage_image", action: "show", layerId: "letter", assetId: "letter", durationMs: 740 }},
                {{ id: "bad", type: "stage_image", action: "show", layerId: "missing", transform: {{ opacity: 5 }} }},
              ] }}],
            }});
            process.stdout.write(JSON.stringify(timeline));
            """
        )
        result = subprocess.run(["node", "-e", script], cwd=ROOT_DIR, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        timeline = json.loads(result.stdout)
        self.assertEqual(timeline["summary"]["eventCount"], 2)
        self.assertEqual(timeline["sceneReports"][0]["events"][0]["durationMs"], 740)
        issue_codes = {issue["code"] for issue in timeline["issues"]}
        self.assertIn("stage_image_missing_asset", issue_codes)
        self.assertIn("stage_image_opacity_too_low", issue_codes)

    def test_presentation_timeline_helpers_export_markdown_and_csv(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorPresentationTimeline;
            const data = {{
              project: {{ title: "Demo Project" }},
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              assetList: [
                {{ id: "bg_classroom", type: "background", name: "黄昏教室", fileExists: true }},
                {{ id: "bgm_opening", type: "bgm", name: "放课后钢琴", fileExists: true }},
                {{ id: "sfx_missing", type: "sfx", name: "坏音效", fileExists: false }},
              ],
              characters: [
                {{ id: "hero", displayName: "蓝白女主" }},
              ],
              scenes: [
                {{
                  id: "scene_start",
                  chapterId: "chapter_1",
                  name: "教室黄昏",
                  blocks: [
                    {{ id: "block_bg", type: "background", assetId: "bg_classroom", transition: "fade", transitionDurationMs: 900 }},
                    {{ id: "block_music", type: "music_play", assetId: "bgm_opening", fadeInMs: 0, fadeOutMs: 1200 }},
                    {{ id: "block_show", type: "character_show", characterId: "hero", transition: "none", stage: {{ scale: 190, opacity: 100 }} }},
                    {{ id: "block_line_1", type: "dialogue", speakerId: "hero", text: "今天也留下来吗？", textSpeed: "slow" }},
                    {{ id: "block_line_2", type: "dialogue", speakerId: "hero", text: "嗯，只待一会儿。" }},
                    {{ id: "block_sfx", type: "sfx_play", assetId: "sfx_missing" }},
                    {{ id: "block_stop", type: "music_stop", fadeOutMs: 0 }},
                  ],
                }},
                {{
                  id: "scene_static",
                  chapterId: "chapter_1",
                  name: "长对白",
                  blocks: [
                    {{ id: "line_1", type: "narration", text: "第一句。" }},
                    {{ id: "line_2", type: "narration", text: "第二句。" }},
                    {{ id: "line_3", type: "narration", text: "第三句。" }},
                    {{ id: "line_4", type: "narration", text: "第四句。" }},
                    {{ id: "line_5", type: "narration", text: "第五句。" }},
                    {{ id: "line_6", type: "narration", text: "第六句。" }},
                    {{ id: "line_7", type: "narration", text: "第七句。" }},
                  ],
                }},
              ],
            }};
            const timeline = tools.buildPresentationTimeline(data);
            const digest = tools.getPresentationTimelineStatusDigest(timeline);
            const markdown = tools.buildPresentationTimelineMarkdown(timeline, {{
              projectTitle: "Demo Project",
              generatedAt: "2026-05-10 23:30:00",
            }});
            const csv = tools.buildPresentationTimelineCsv(timeline);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              timeline,
              digest,
              markdown,
              csv,
              slowTextMs: tools.estimateTextDurationMs({{ type: "dialogue", text: "一二三四五六", textSpeed: "slow" }}),
              formatted: tools.formatDuration(65000),
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
        self.assertIn("buildPresentationTimeline", payload["keys"])
        self.assertIn("buildPresentationTimelineMarkdown", payload["keys"])
        self.assertIn("buildPresentationTimelineCsv", payload["keys"])
        self.assertEqual(payload["timeline"]["summary"]["sceneCount"], 2)
        self.assertEqual(payload["timeline"]["summary"]["storySceneCount"], 2)
        self.assertEqual(payload["timeline"]["summary"]["eventCount"], 14)
        self.assertEqual(payload["timeline"]["summary"]["longStaticTextRunCount"], 1)
        self.assertEqual(payload["timeline"]["summary"]["abruptAudioCount"], 2)
        self.assertEqual(payload["digest"]["status"], "blocked")
        issue_codes = [issue["code"] for issue in payload["timeline"]["issues"]]
        self.assertIn("sfx_asset_not_ready", issue_codes)
        self.assertIn("long_static_text_run", issue_codes)
        self.assertIn("scene_opening_without_background", issue_codes)
        self.assertIn("character_show_hard_cut", issue_codes)
        self.assertIn("# Demo Project 演出时间轴", payload["markdown"])
        self.assertIn("长对白", payload["markdown"])
        self.assertIn('"放课后钢琴"', payload["csv"])
        self.assertEqual(payload["formatted"], "1 分 5 秒")
        self.assertGreater(payload["slowTextMs"], 0)


if __name__ == "__main__":
    unittest.main()
