from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "dashboard_production.js"


class FrontendDashboardProductionModuleTests(unittest.TestCase):
    def test_dashboard_production_rules_prioritize_next_steps_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorDashboardProduction;
            const helpers = {{
              getSafeScenePriority(value) {{
                return ["parked", "normal", "focus", "rush"].includes(value) ? value : "normal";
              }},
              getSafeSceneStatus(value) {{
                return ["outline", "drafting", "polishing", "ready"].includes(value) ? value : "outline";
              }},
              getScenePriorityLabel(value) {{
                return {{ parked: "先放一放", normal: "正常推进", focus: "优先处理", rush: "马上处理" }}[value] || "正常推进";
              }},
              getSceneStatusLabel(value) {{
                return {{ outline: "待开写", drafting: "写作中", polishing: "润色中", ready: "可试玩" }}[value] || "待开写";
              }},
              buildRouteSceneProductionNotes(scene) {{
                return scene.productionNotes || [];
              }},
            }};
            const routeOverview = {{
              metrics: {{ brokenRoutes: 1, unreachableScenes: 2 }},
              alerts: [
                {{ tone: "danger", label: "坏链", sceneName: "屋顶", sceneId: "scene_roof", meta: "jump missing" }},
                {{ tone: "warn", label: "不可达", sceneName: "尾声", sceneId: "scene_ending", meta: "入口走不到" }},
              ],
              nodes: [
                {{
                  id: "scene_rush",
                  name: "告白",
                  chapterName: "第1章",
                  priority: "rush",
                  status: "polishing",
                  dialogueCount: 3,
                  narrationCount: 1,
                  choiceCount: 1,
                  completionScore: 66,
                  hasStoryContent: true,
                  hasBackground: true,
                  hasMusic: false,
                  hasEffects: true,
                  missingVoiceCount: 2,
                  notes: "今天先搞定",
                }},
                {{
                  id: "scene_ready",
                  name: "尾声",
                  chapterName: "第1章",
                  priority: "normal",
                  status: "ready",
                  dialogueCount: 1,
                  narrationCount: 0,
                  choiceCount: 0,
                  completionScore: 90,
                  hasStoryContent: true,
                  hasBackground: true,
                  hasMusic: true,
                  hasEffects: true,
                  missingVoiceCount: 0,
                  productionNotes: ["可以做最终试玩"],
                }},
                {{
                  id: "scene_parked",
                  name: "支线",
                  chapterName: "第1章",
                  priority: "parked",
                  status: "drafting",
                  dialogueCount: 0,
                  narrationCount: 0,
                  choiceCount: 0,
                  completionScore: 5,
                  hasStoryContent: false,
                  hasBackground: false,
                  hasMusic: false,
                  hasEffects: false,
                }},
              ],
            }};
            const overview = {{
              plannedScenes: tools.buildDashboardScenePlanningQueue(routeOverview, helpers),
              emptyScenes: [{{ id: "scene_empty", name: "空教室" }}],
              scenesMissingBackground: [{{ id: "scene_no_bg", name: "走廊" }}],
              scenesMissingMusic: [{{ id: "scene_no_bgm", name: "天台" }}],
              flatScenes: [{{ id: "scene_flat", name: "普通告别" }}],
              missingVoiceCount: 4,
              voiceProgress: 60,
              issueEntryCount: 3,
              issueEntries: [
                {{ title: "占位台词", sceneId: "scene_rush", blockId: "line_1", issues: ["placeholder"] }},
                {{ title: "长台词", sceneId: "scene_ready", blockId: "line_2", issues: ["too_long"] }},
              ],
              unusedAssets: [{{ id: "asset_unused", name: "备用 BGM" }}],
              directionIdeaCount: 2,
            }};
            const tasks = tools.buildDashboardProductionTasks(routeOverview, overview, {{
              helpers,
              validationErrors: [
                {{ message: "角色引用不存在", location: "scene_rush / line_1" }},
              ],
            }});
            const columns = tools.buildDashboardSceneStatusColumns(routeOverview, helpers);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              progress: [
                tools.getDashboardProgressPercent(1, 4),
                tools.getDashboardProgressPercent(0, 0),
              ],
              summaries: [
                tools.buildDashboardProductionSummary({{ readinessScore: 80, routeOverview: {{ metrics: {{ brokenRoutes: 1 }} }} }}),
                tools.buildDashboardProductionSummary({{ readinessScore: 80, routeOverview: {{ metrics: {{}} }}, issueEntryCount: 0, missingVoiceCount: 0, directionIdeaCount: 0 }}),
              ],
              queue: overview.plannedScenes.map((scene) => ({{
                id: scene.id,
                tone: scene.tone,
                summary: scene.summary,
                nextStep: scene.nextStep,
                checklist: scene.playableChecklist,
                actionPlan: scene.playableActionPlan,
              }})),
              emptyChecklist: tools.buildDashboardScenePlayableChecklist(routeOverview.nodes[2]),
              emptyActionPlan: tools.buildDashboardScenePlayableActionPlan(
                routeOverview.nodes[2],
                tools.buildDashboardScenePlayableChecklist(routeOverview.nodes[2])
              ),
              musicFocusHint: tools.getSceneChecklistFocusHint("music", "补 BGM"),
              voiceFocusHint: tools.getSceneChecklistFocusHint("voice", "补语音"),
              presentationFocusHint: tools.getSceneChecklistFocusHint("presentation", "加镜头 / 特效"),
              customFocusHint: tools.getSceneChecklistFocusHint("custom_gap", "补自定义"),
              emptyFocusHint: tools.getSceneChecklistFocusHint("custom_gap", ""),
              tasks: tasks.map((task) => ({{
                title: task.title,
                priority: task.priority,
                tone: task.tone,
                badge: task.badge,
                action: task.actions?.[0]?.action,
                actions: (task.actions || []).map((action) => ({{
                  label: action.label,
                  action: action.action,
                  sceneId: action.sceneId || "",
                  screen: action.screen || "",
                  dataset: action.dataset || {{}},
                }})),
              }})),
              columns: columns.map((column) => ({{
                status: column.status,
                count: column.scenes.length,
                firstId: column.scenes[0]?.id || "",
              }})),
              toneClasses: [
                tools.getDashboardTaskToneClass("danger"),
                tools.getDashboardTaskToneClass("warn"),
                tools.getDashboardTaskToneClass("good"),
                tools.getDashboardTaskToneClass("soft"),
              ],
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

        self.assertIn("buildDashboardProductionTasks", payload["keys"])
        self.assertIn("buildDashboardScenePlayableActionPlan", payload["keys"])
        self.assertIn("buildDashboardScenePlayableChecklist", payload["keys"])
        self.assertIn("getSceneChecklistFocusHint", payload["keys"])
        self.assertEqual(payload["progress"], [25, 100])
        self.assertIn("路线断线", payload["summaries"][0])
        self.assertIn("成品味道", payload["summaries"][1])
        self.assertEqual(payload["queue"][0]["id"], "scene_rush")
        self.assertEqual(payload["queue"][0]["tone"], "danger")
        self.assertIn("润色中", payload["queue"][0]["summary"])
        self.assertEqual(payload["queue"][0]["checklist"]["status"], "needs_core")
        self.assertEqual(payload["queue"][0]["checklist"]["score"], 60)
        self.assertIn("补 BGM", payload["queue"][0]["checklist"]["nextStep"])
        self.assertEqual(payload["queue"][0]["checklist"]["items"][2]["action"]["action"], "open-scene-from-map")
        self.assertEqual(payload["queue"][0]["checklist"]["items"][2]["action"]["sceneId"], "scene_rush")
        self.assertEqual(payload["queue"][0]["checklist"]["items"][2]["action"]["label"], "补 BGM")
        self.assertEqual(payload["queue"][0]["actionPlan"][0]["action"], "open-scene-from-map")
        self.assertEqual(payload["queue"][0]["actionPlan"][0]["sceneId"], "scene_rush")
        self.assertEqual(payload["queue"][0]["actionPlan"][0]["dataset"]["scene-checklist-item"], "music")
        self.assertEqual(payload["queue"][0]["actionPlan"][0]["dataset"]["scene-checklist-label"], "补 BGM")
        self.assertEqual(payload["queue"][1]["checklist"]["status"], "ready")
        self.assertEqual(payload["queue"][1]["checklist"]["score"], 100)
        self.assertIsNone(payload["queue"][1]["checklist"]["items"][2]["action"])
        self.assertEqual(payload["queue"][1]["actionPlan"][0]["action"], "preview-scene-from-map")
        self.assertEqual(payload["queue"][1]["actionPlan"][0]["sceneId"], "scene_ready")
        self.assertEqual(payload["emptyChecklist"]["status"], "needs_core")
        self.assertIn("先补正文", payload["emptyChecklist"]["nextStep"])
        self.assertEqual(payload["emptyActionPlan"][0]["action"], "apply-story-template-to-scene")
        self.assertEqual(payload["emptyActionPlan"][0]["dataset"]["template-id"], "playable_scene")
        self.assertEqual(payload["emptyActionPlan"][0]["dataset"]["scene-id"], "scene_parked")
        self.assertEqual(payload["musicFocusHint"]["title"], "补 BGM")
        self.assertIn("音乐范围卡", payload["musicFocusHint"]["description"])
        self.assertEqual(payload["musicFocusHint"]["actions"][0]["action"], "add-music-play")
        self.assertTrue(payload["musicFocusHint"]["actions"][0]["primary"])
        self.assertEqual(payload["musicFocusHint"]["actions"][0]["dataset"]["scene-checklist-complete"], "music")
        self.assertEqual(payload["voiceFocusHint"]["actions"][0]["action"], "focus-story-block-filters")
        self.assertEqual(payload["voiceFocusHint"]["actions"][0]["dataset"]["story-block-issue"], "missing_voice")
        self.assertNotIn("scene-checklist-complete", payload["voiceFocusHint"]["actions"][0]["dataset"])
        self.assertEqual(
            [action["action"] for action in payload["presentationFocusHint"]["actions"]],
            ["add-camera-zoom", "add-particle-effect", "add-screen-fade"],
        )
        self.assertTrue(
            all(
                action["dataset"]["scene-checklist-complete"] == "presentation"
                for action in payload["presentationFocusHint"]["actions"]
            )
        )
        self.assertEqual(payload["customFocusHint"]["title"], "补自定义")
        self.assertEqual(payload["customFocusHint"]["actions"], [])
        self.assertIsNone(payload["emptyFocusHint"])
        self.assertNotIn("scene_parked", [scene["id"] for scene in payload["queue"]])
        self.assertEqual(payload["tasks"][0]["title"], "先修路线断线")
        self.assertEqual(payload["tasks"][1]["title"], "先处理结构问题")
        self.assertIn("跟进你手动标记的重点场景", [task["title"] for task in payload["tasks"]])
        self.assertIn("清一轮无用素材", [task["title"] for task in payload["tasks"]])
        task_by_title = {task["title"]: task for task in payload["tasks"]}
        self.assertEqual(task_by_title["补可试玩正文"]["actions"][0]["action"], "apply-story-template-to-scene")
        self.assertEqual(task_by_title["补可试玩正文"]["actions"][0]["dataset"]["template-id"], "playable_scene")
        self.assertEqual(task_by_title["补可试玩正文"]["actions"][0]["dataset"]["scene-id"], "scene_empty")
        self.assertEqual(task_by_title["补可试玩正文"]["actions"][1]["action"], "open-scene-from-map")
        self.assertEqual(task_by_title["补可试玩正文"]["actions"][1]["dataset"]["scene-checklist-item"], "story")
        self.assertEqual(task_by_title["给场景补舞台感"]["actions"][0]["label"], "打开并补背景")
        self.assertEqual(task_by_title["给场景补舞台感"]["actions"][0]["sceneId"], "scene_no_bg")
        self.assertEqual(task_by_title["给场景补舞台感"]["actions"][0]["dataset"]["scene-checklist-item"], "background")
        self.assertEqual(task_by_title["给关键场景补 BGM"]["actions"][0]["label"], "打开并补 BGM")
        self.assertEqual(task_by_title["给关键场景补 BGM"]["actions"][0]["sceneId"], "scene_no_bgm")
        self.assertEqual(task_by_title["给关键场景补 BGM"]["actions"][0]["dataset"]["scene-checklist-item"], "music")
        self.assertEqual(payload["columns"][2]["status"], "polishing")
        self.assertEqual(payload["columns"][2]["firstId"], "scene_rush")
        self.assertEqual(payload["columns"][3]["firstId"], "scene_ready")
        self.assertEqual(payload["toneClasses"], ["danger-text", "warn-text", "good-text", ""])


if __name__ == "__main__":
    unittest.main()
