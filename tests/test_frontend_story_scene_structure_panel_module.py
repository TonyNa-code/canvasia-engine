from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_scene_structure_panel.js"


class FrontendStorySceneStructurePanelModuleTests(unittest.TestCase):
    def test_story_scene_structure_panel_renders_playable_gate_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStorySceneStructurePanel;
            const helpers = {{
              escapeHtml(value) {{
                return String(value ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
              }},
              getDashboardTaskToneClass(tone) {{
                return `${{tone}}-text`;
              }},
              renderEmpty(text) {{
                return `<empty>${{text}}</empty>`;
              }},
              renderRouteMetricCard(label, value, hint) {{
                return `<metric data-label="${{label}}" data-value="${{value}}">${{hint}}</metric>`;
              }},
            }};
            const scene = {{ id: "scene_1", status: "draft", priority: "high" }};
            const overview = {{
              completionScore: 72,
              storyCount: 4,
              dialogueCount: 2,
              narrationCount: 1,
              choiceCount: 1,
              conditionCount: 0,
              effectCount: 1,
              logicCount: 1,
              issueBlockCount: 1,
              issueCounts: {{ any: 1, missing_voice: 1, missing_asset: 0, broken_target: 0, too_long: 0 }},
              hasStoryContent: true,
              hasBackground: true,
              hasMusic: false,
              hasEffects: true,
              routes: [{{ targetSceneId: "scene_2", targetExists: true }}],
              branchTargetCount: 1,
              brokenRouteCount: 0,
              productionNotes: ["缺 BGM 规划"],
              phaseLabel: "铺垫后分线",
              sceneSummary: "这场已经能读，但还可以补音乐。",
              structureNotes: ["第 4 张开始出现分支或条件"],
              highlightCandidates: [
                {{
                  blockId: "block_<1>",
                  index: 3,
                  tone: "warn",
                  blockLabel: "选项 <分支>",
                  title: "是否一起回家",
                  reason: "这里会把剧情推向不同走向",
                  meta: "选项 2",
                }},
              ],
              nextSteps: ["补 BGM 范围，让氛围更完整。"],
            }};
            const html = tools.renderStorySceneStructurePanel(scene, overview, {{
              ...helpers,
              moodRecipePanelHtml: "<recipe>mood</recipe>",
              scenePriorityLabel: "高优先级",
              sceneStatusLabel: "写作中",
              tone: "warn",
            }});
            const optimizer = tools.renderStorySceneOptimizerSection(scene, overview, {{
              ...helpers,
              polishDigest: {{
                actionLabel: "演出已经比较稳",
                canApply: false,
                tags: ["已经有演出"],
                helperText: "节奏体检：可以试玩，建议补 BGM 范围。",
              }},
            }});
            const playableGate = tools.buildStoryScenePlayableGate(overview);
            const brokenGate = tools.buildStoryScenePlayableGate({{
              ...overview,
              issueCounts: {{ ...overview.issueCounts, broken_target: 1 }},
              brokenRouteCount: 1,
            }});
            const noContentPlan = tools.buildStoryScenePlayableActionPlan(scene, {{
              ...overview,
              storyCount: 0,
              hasStoryContent: false,
              hasBackground: false,
              hasMusic: false,
              routes: [],
              issueCounts: {{}},
            }});
            const playablePlan = tools.buildStoryScenePlayableActionPlan(scene, overview);
            const brokenPlan = tools.buildStoryScenePlayableActionPlan(scene, {{
              ...overview,
              issueCounts: {{ ...overview.issueCounts, broken_target: 1 }},
              brokenRouteCount: 1,
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              html,
              optimizer,
              playableGate,
              brokenGate,
              noContentPlan,
              playablePlan,
              brokenPlan,
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
        html = payload["html"]
        optimizer = payload["optimizer"]

        self.assertIn("buildStoryScenePlayableGate", payload["keys"])
        self.assertIn("buildStoryScenePlayableActionPlan", payload["keys"])
        self.assertIn("renderStorySceneStructurePanel", payload["keys"])
        self.assertIn("场景结构总览", html)
        self.assertIn("可试玩闸门", html)
        self.assertIn("推荐顺序", html)
        self.assertEqual(payload["playableGate"]["label"], "已可试玩，建议补 BGM")
        self.assertEqual(payload["brokenGate"]["tone"], "danger")
        self.assertEqual(payload["noContentPlan"][0]["action"], "apply-story-template")
        self.assertEqual(payload["noContentPlan"][0]["dataset"]["template-id"], "playable_scene")
        self.assertEqual(payload["brokenPlan"][0]["action"], "focus-story-block-filters")
        self.assertEqual(payload["brokenPlan"][0]["dataset"]["story-block-issue"], "broken_target")
        self.assertEqual(payload["playablePlan"][0]["action"], "add-music-play")
        self.assertEqual(payload["playablePlan"][1]["action"], "preview-scene-from-map")
        self.assertEqual(payload["playablePlan"][1]["dataset"]["scene-id"], "scene_1")
        self.assertIn("BGM：建议补一段 BGM", html)
        self.assertIn('data-action="add-music-play"', html)
        self.assertIn('data-action="preview-scene-from-map"', html)
        self.assertIn('data-scene-id="scene_1"', html)
        self.assertIn("写作中 / 高优先级", html)
        self.assertIn("铺垫后分线", html)
        self.assertIn("缺 BGM 规划", html)
        self.assertIn("选项 &lt;分支&gt;", html)
        self.assertIn('data-block-id="block_&lt;1&gt;"', html)
        self.assertIn("<recipe>mood</recipe>", html)
        self.assertIn("补 BGM 范围，让氛围更完整。", html)
        self.assertIn("场景优化助手", optimizer)
        self.assertIn("只看待绑语音（1）", optimizer)
        self.assertIn("演出已经比较稳", optimizer)
        self.assertIn("节奏体检：可以试玩，建议补 BGM 范围。", optimizer)
        self.assertIn("disabled", optimizer)


if __name__ == "__main__":
    unittest.main()
