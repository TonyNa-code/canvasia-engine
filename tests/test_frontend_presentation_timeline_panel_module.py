from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_COMMON_PATH = ROOT_DIR / "prototype_editor" / "modules" / "editor_common.js"
TIMELINE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "presentation_timeline.js"
PANEL_PATH = ROOT_DIR / "prototype_editor" / "modules" / "presentation_timeline_panel.js"


class FrontendPresentationTimelinePanelModuleTests(unittest.TestCase):
    def test_presentation_timeline_panel_renders_rehearsal_queue_and_states(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            for (const filePath of [
              {json.dumps(str(EDITOR_COMMON_PATH))},
              {json.dumps(str(TIMELINE_PATH))},
              {json.dumps(str(PANEL_PATH))},
            ]) {{
              vm.runInContext(fs.readFileSync(filePath, "utf8"), context);
            }}
            const timelineTools = context.window.CanvasiaEditorPresentationTimeline;
            const panelTools = context.window.CanvasiaEditorPresentationTimelinePanel;
            const issueTimeline = timelineTools.buildPresentationTimeline({{
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              assetList: [
                {{ id: "bgm_opening", type: "bgm", name: "放课后钢琴", fileExists: true }},
                {{ id: "sfx_missing", type: "sfx", name: "坏音效", fileExists: false }},
              ],
              characters: [{{ id: "hero", displayName: "蓝白女主" }}],
              scenes: [
                {{
                  id: "scene_start",
                  chapterId: "chapter_1",
                  name: "教室黄昏",
                  blocks: [
                    {{ id: "music_1", type: "music_play", assetId: "bgm_opening", fadeInMs: 0 }},
                    {{ id: "show_1", type: "character_show", characterId: "hero", transition: "none" }},
                    {{ id: "line_1", type: "dialogue", speakerId: "hero", text: "今天也留下来吗？" }},
                    {{ id: "sfx_1", type: "sfx_play", assetId: "sfx_missing" }},
                    {{ id: "stop_1", type: "music_stop", fadeOutMs: 0 }},
                  ],
                }},
              ],
            }});
            const readyTimeline = timelineTools.buildPresentationTimeline({{
              chapters: [{{ id: "chapter_1", name: "第1章" }}],
              assetList: [
                {{ id: "bg_classroom", type: "background", name: "黄昏教室", fileExists: true }},
                {{ id: "bgm_opening", type: "bgm", name: "放课后钢琴", fileExists: true }},
              ],
              characters: [{{ id: "hero", displayName: "蓝白女主" }}],
              scenes: [
                {{
                  id: "scene_ready",
                  chapterId: "chapter_1",
                  name: "放学后",
                  blocks: [
                    {{ id: "bg_1", type: "background", assetId: "bg_classroom", transition: "fade", transitionDurationMs: 600 }},
                    {{ id: "music_1", type: "music_play", assetId: "bgm_opening", fadeInMs: 700, fadeOutMs: 900 }},
                    {{ id: "show_1", type: "character_show", characterId: "hero", transition: "fade", transitionDurationMs: 600 }},
                    {{ id: "line_1", type: "dialogue", speakerId: "hero", text: "欢迎回来。" }},
                  ],
                }},
              ],
            }});
            const emptyHtml = panelTools.renderPresentationTimelinePanel({{ summary: {{}}, issues: [], sceneReports: [] }});
            const issueHtml = panelTools.renderPresentationTimelinePanel(issueTimeline);
            const readyHtml = panelTools.renderPresentationTimelinePanel(readyTimeline);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(panelTools).sort(),
              rehearsalRows: panelTools.buildPresentationRehearsalRows(issueTimeline, 4),
              emptyHtml,
              issueHtml,
              readyHtml,
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
        self.assertIn("renderPresentationTimelinePanel", payload["keys"])
        self.assertIn("renderPresentationRehearsalQueue", payload["keys"])
        self.assertIn("buildPresentationRehearsalRows", payload["keys"])
        self.assertGreaterEqual(len(payload["rehearsalRows"]), 1)
        self.assertIn("演出时间轴", payload["issueHtml"])
        self.assertIn("排练优先队列", payload["issueHtml"])
        self.assertIn("先修阻塞，再跑最长段落", payload["issueHtml"])
        self.assertIn("音效素材不可用", payload["issueHtml"])
        self.assertIn("sfx_missing", payload["issueHtml"])
        self.assertIn("BGM 进入过快", payload["issueHtml"])
        self.assertIn("视觉 / 音频锚点", payload["issueHtml"])
        self.assertIn('data-action="export-presentation-timeline-markdown"', payload["issueHtml"])
        self.assertIn('data-action="export-presentation-timeline-csv"', payload["issueHtml"])
        self.assertIn("放学后", payload["readyHtml"])
        self.assertIn("完整排练：放学后", payload["readyHtml"])
        self.assertIn("当前项目还没有可列出的演出时间轴", payload["emptyHtml"])


if __name__ == "__main__":
    unittest.main()
