from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "preview_story_debugger.js"


class FrontendPreviewStoryDebuggerModuleTests(unittest.TestCase):
    def run_module_script(self, body: str) -> dict:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorPreviewStoryDebugger;
            {body}
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
        return json.loads(completed.stdout)

    def test_route_and_coverage_ignore_abandoned_future_timeline(self) -> None:
        payload = self.run_module_script(
            """
            const projectData = {
              chapters: [{ id: "chapter_1", name: "第一章", scenes: [
                { id: "scene_start", name: "教室", chapterName: "第一章", blocks: [
                  { id: "choice_1", type: "choice", options: [
                    { id: "opt_a", text: "留下", gotoSceneId: "scene_gate" },
                    { id: "opt_b", text: "离开", gotoSceneId: "scene_end" },
                  ] },
                ] },
                { id: "scene_gate", name: "走廊", chapterName: "第一章", blocks: [
                  { id: "condition_1", type: "condition", branches: [
                    { id: "route_a", when: [{ variableId: "affection", operator: ">=", value: 2 }], gotoSceneId: "scene_end" },
                  ], elseGotoSceneId: "scene_start" },
                ] },
                { id: "scene_end", name: "天台", chapterName: "第一章", blocks: [] },
              ] }],
              scenesById: new Map([
                ["scene_start", { name: "教室" }],
                ["scene_gate", { name: "走廊" }],
                ["scene_end", { name: "天台" }],
              ]),
            };
            const session = {
              position: 2,
              timeline: [
                { sceneId: "scene_start", sceneName: "教室", blockId: "choice_1", blockType: "choice", selectedOptionId: "opt_a", routeDecision: { title: "已选：留下", meta: "去走廊" } },
                { sceneId: "scene_gate", sceneName: "走廊", blockId: "condition_1", blockType: "condition", resolvedBranchId: "route_a", routeDecision: { title: "命中：好感度", meta: "去天台" } },
                { sceneId: "scene_end", sceneName: "天台", blockId: "line_1", blockType: "dialogue" },
                { sceneId: "scene_start", sceneName: "教室", blockId: "choice_1", blockType: "choice", selectedOptionId: "opt_b", routeDecision: { title: "已选：离开", meta: "去天台" } },
              ],
            };
            const options = {
              getRouteDecisionSummary: (snapshot) => snapshot.routeDecision || null,
              getConditionBranchKey: (branch, index) => branch.id || `branch-${index + 1}`,
              formatConditionRule: () => "好感度 >= 2",
              getChoiceTargetLabel: (sceneId) => projectData.scenesById.get(sceneId)?.name || sceneId,
            };
            const route = tools.buildPreviewRouteSummary(session, options);
            const coverage = tools.buildPreviewBranchCoverage(session, projectData, options);
            process.stdout.write(JSON.stringify({
              activeLength: tools.getActivePreviewTimeline(session).length,
              route,
              coverage,
            }));
            """
        )

        self.assertEqual(payload["activeLength"], 3)
        self.assertEqual(payload["route"]["choiceCount"], 1)
        self.assertEqual(payload["route"]["conditionCount"], 1)
        self.assertNotIn("离开", json.dumps(payload["route"], ensure_ascii=False))
        choice_point = next(point for point in payload["coverage"]["points"] if point["blockType"] == "choice")
        self.assertTrue(next(item for item in choice_point["outcomes"] if item["label"] == "留下")["covered"])
        self.assertFalse(next(item for item in choice_point["outcomes"] if item["label"] == "离开")["covered"])
        self.assertEqual(payload["coverage"]["coveredOutcomeCount"], 2)

    def test_flight_recorder_tracks_variable_and_stage_changes_and_exports_markdown(self) -> None:
        payload = self.run_module_script(
            """
            const session = {
              startSceneId: "scene_start",
              position: 2,
              timeline: [
                {
                  sceneId: "scene_start", sceneName: "教室", blockId: "bg_1", blockIndex: 0, blockType: "background",
                  block: { id: "bg_1", type: "background", assetId: "bg_classroom" }, variables: { affection: 0 },
                  visualState: { backgroundAssetId: "bg_classroom", backgroundName: "黄昏教室", visibleCharacters: [], visibleStageImages: [] },
                },
                {
                  sceneId: "scene_start", sceneName: "教室", blockId: "var_1", blockIndex: 1, blockType: "variable_add",
                  block: { id: "var_1", type: "variable_add" }, variables: { affection: 2 },
                  visualState: { backgroundAssetId: "bg_classroom", backgroundName: "黄昏教室", visibleCharacters: [], visibleStageImages: [] },
                },
                {
                  sceneId: "scene_start", sceneName: "教室", blockId: "music_1", blockIndex: 2, blockType: "music_play",
                  block: { id: "music_1", type: "music_play", assetId: "bgm_after_school" }, variables: { affection: 2 },
                  visualState: {
                    backgroundAssetId: "bg_classroom", backgroundName: "黄昏教室", musicAssetId: "bgm_after_school", musicName: "放课后钢琴", musicVolume: 72,
                    visibleCharacters: [{ characterId: "hero", position: "center", expressionName: "微笑" }],
                    visibleStageImages: [{ layerId: "letter", assetId: "letter_cg", position: "center" }],
                  },
                  routeDecision: { title: "命中：好感度路线", meta: "去天台", pending: false },
                },
                {
                  sceneId: "discarded", sceneName: "废弃未来", blockId: "future", blockIndex: 0, blockType: "dialogue",
                  variables: { affection: 99 }, visualState: { musicAssetId: "future_bgm" },
                },
              ],
            };
            const report = tools.buildPreviewFlightRecorder(session, {
              projectTitle: "Demo Project",
              generatedAt: "2026-07-26T10:00:00.000Z",
              variableDefinitions: [{ id: "affection", name: "好感度", type: "number", defaultValue: 0 }],
              blockLabels: { background: "切换背景", variable_add: "增加变量", music_play: "播放音乐" },
              getRouteDecisionSummary: (snapshot) => snapshot.routeDecision || null,
              getBlockSummary: (snapshot) => ({ title: `卡片 ${snapshot.blockId}`, meta: "测试" }),
              getCharacterName: () => "蓝白女主",
              getAssetName: (assetId) => ({ bg_classroom: "黄昏教室", bgm_after_school: "放课后钢琴", letter_cg: "信件" }[assetId] || assetId),
            });
            const markdown = tools.buildPreviewFlightRecorderMarkdown(report);
            process.stdout.write(JSON.stringify({ report, markdown }));
            """
        )

        report = payload["report"]
        self.assertEqual(report["summary"]["stepCount"], 3)
        self.assertEqual(report["summary"]["variableChangeCount"], 1)
        self.assertGreaterEqual(report["summary"]["stageCueCount"], 4)
        self.assertEqual(report["summary"]["routeDecisionCount"], 1)
        self.assertEqual(report["entries"][1]["variableChanges"][0]["beforeLabel"], "0")
        self.assertEqual(report["entries"][1]["variableChanges"][0]["afterLabel"], "2")
        cue_labels = {cue["label"] for cue in report["entries"][2]["stageCues"]}
        self.assertIn("BGM 开始", cue_labels)
        self.assertIn("角色登场", cue_labels)
        self.assertIn("舞台贴图出现", cue_labels)
        self.assertIn("Demo Project 试玩飞行记录", payload["markdown"])
        self.assertIn("好感度: 0 -> 2", payload["markdown"])
        self.assertIn("当前时间线位置之前的有效轨迹", payload["markdown"])
        self.assertNotIn("废弃未来", payload["markdown"])


if __name__ == "__main__":
    unittest.main()
