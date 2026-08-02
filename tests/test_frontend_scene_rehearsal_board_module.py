from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "scene_rehearsal_board.js"
CATALOG_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_catalog.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"
INDEX_PATH = ROOT_DIR / "prototype_editor" / "index.html"


class FrontendSceneRehearsalBoardModuleTests(unittest.TestCase):
    def run_node(self, body: str) -> dict:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(CATALOG_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorSceneRehearsalBoard;
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

    def test_rehearsal_model_aligns_story_stage_audio_motion_and_route_lanes(self) -> None:
        payload = self.run_node(
            """
            const scene = {
              id: "scene_rooftop",
              name: "屋顶晚风",
              chapterName: "第一章",
              blocks: [
                { id: "bg", type: "background", assetId: "bg_rooftop" },
                { id: "show", type: "character_show", characterId: "heroine" },
                { id: "bgm", type: "music_play", assetId: "bgm_evening" },
                { id: "line", type: "dialogue", text: "你终于来了。", voiceAssetId: "voice_001" },
                { id: "zoom", type: "camera_zoom", direction: "in" },
                { id: "choice", type: "choice", options: [{ text: "握住她的手" }] },
                { id: "jump", type: "jump", targetSceneId: "ending" },
              ],
            };
            const report = {
              events: [
                { blockId: "bg", blockIndex: 0, durationMs: 600 },
                { blockId: "show", blockIndex: 1, durationMs: 500 },
                { blockId: "bgm", blockIndex: 2, durationMs: 0 },
                { blockId: "line", blockIndex: 3, durationMs: 2400 },
                { blockId: "zoom", blockIndex: 4, durationMs: 820 },
                { blockId: "choice", blockIndex: 5, durationMs: 1600 },
                { blockId: "jump", blockIndex: 6, durationMs: 0 },
              ],
              issues: [
                { blockId: "zoom", blockIndex: 4, severity: "warn", title: "镜头偏密", detail: "复查节奏" },
              ],
            };
            const model = tools.buildSceneRehearsalModel(scene, report, {
              selectedBlockId: "line",
              blockLabels: { dialogue: "台词", background: "背景", character_show: "角色登场", music_play: "播放 BGM", camera_zoom: "镜头缩放", choice: "选项", jump: "跳转" },
              getBlockSummary: (block) => ({ title: block.text || block.assetId || block.type, meta: `meta:${block.id}` }),
              formatDuration: (ms) => `${ms}ms`,
            });
            process.stdout.write(JSON.stringify({
              keys: Object.keys(tools).sort(),
              scene: [model.sceneId, model.sceneName, model.chapterName],
              summary: model.summary,
              selected: [model.selectedBeat.blockId, model.selectedBeat.startMs, model.selectedBeat.startTimecode, model.selectedBeat.durationLabel],
              neighborIds: [model.previousBeat.blockId, model.nextBeat.blockId],
              lineLanes: model.beats.find((beat) => beat.blockId === "line").lanes,
              choiceLanes: model.beats.find((beat) => beat.blockId === "choice").lanes,
              laneCounts: Object.fromEntries(model.laneRows.map((lane) => [lane.id, lane.markerCount])),
              zoomStatus: model.beats.find((beat) => beat.blockId === "zoom").status,
              timecodes: [tools.formatTimecode(0), tools.formatTimecode(61234)],
            }));
            """
        )

        self.assertIn("buildSceneRehearsalModel", payload["keys"])
        self.assertIn("renderSceneRehearsalBoard", payload["keys"])
        self.assertEqual(payload["scene"], ["scene_rooftop", "屋顶晚风", "第一章"])
        self.assertEqual(payload["summary"]["beatCount"], 7)
        self.assertEqual(payload["summary"]["estimatedDurationMs"], 5920)
        self.assertEqual(payload["summary"]["activeLaneCount"], 5)
        self.assertEqual(payload["summary"]["voicedBeatCount"], 1)
        self.assertEqual(payload["selected"], ["line", 1100, "00:01.1", "2400ms"])
        self.assertEqual(payload["neighborIds"], ["bgm", "zoom"])
        self.assertEqual(payload["lineLanes"], ["story", "audio"])
        self.assertEqual(payload["choiceLanes"], ["story", "logic"])
        self.assertEqual(payload["laneCounts"], {"story": 2, "stage": 2, "audio": 2, "motion": 1, "logic": 2})
        self.assertEqual(payload["zoomStatus"], "warn")
        self.assertEqual(payload["timecodes"], ["00:00.0", "01:01.2"])

    def test_every_registered_story_card_has_an_explicit_rehearsal_lane(self) -> None:
        payload = self.run_node(
            """
            const catalog = context.window.CanvasiaEditorStoryBlockCatalog;
            const registeredTypes = catalog.getKnownBlockTypes();
            const laneTypes = Object.keys(tools.BLOCK_LANES);
            process.stdout.write(JSON.stringify({
              registeredCount: registeredTypes.length,
              missing: registeredTypes.filter((type) => !tools.BLOCK_LANES[type]),
              unknown: laneTypes.filter((type) => !catalog.isKnownStoryBlockType(type)),
              invalidLanes: laneTypes.filter((type) =>
                tools.BLOCK_LANES[type].some((lane) => !tools.REHEARSAL_LANES.some((entry) => entry.id === lane))
              ),
            }));
            """
        )

        self.assertGreaterEqual(payload["registeredCount"], 31)
        self.assertEqual(payload["missing"], [])
        self.assertEqual(payload["unknown"], [])
        self.assertEqual(payload["invalidLanes"], [])

    def test_rehearsal_board_windows_large_scenes_and_renders_accessible_actions(self) -> None:
        payload = self.run_node(
            """
            const blocks = Array.from({ length: 80 }, (_, index) => ({
              id: `line_${index + 1}`,
              type: index % 9 === 0 ? "camera_pan" : "dialogue",
              text: `第 ${index + 1} 句`,
              voiceAssetId: index === 63 ? "voice_64" : "",
            }));
            const scene = { id: "long_scene", name: "长场景", chapterName: "第二章", blocks };
            const report = {
              events: blocks.map((block, blockIndex) => ({ blockId: block.id, blockIndex, durationMs: block.type === "dialogue" ? 900 : 500 })),
              issues: [{ blockId: "line_64", blockIndex: 63, severity: "blocker", title: "缺少关键素材", detail: "先补文件" }],
            };
            const options = {
              selectedBlockId: "line_64",
              maxVisibleBeats: 20,
              expanded: true,
              getBlockSummary: (block) => ({ title: block.text, meta: `第 ${block.id.split("_")[1]} 拍` }),
              formatDuration: (ms) => `${Math.round(ms / 100) / 10} 秒`,
            };
            const model = tools.buildSceneRehearsalModel(scene, report, options);
            const expandedHtml = tools.renderSceneRehearsalBoard(scene, report, options);
            const collapsedHtml = tools.renderSceneRehearsalBoard(scene, report, { ...options, expanded: false });
            const emptyHtml = tools.renderSceneRehearsalBoard({ id: "empty", name: "空场景", blocks: [] }, {}, {});
            process.stdout.write(JSON.stringify({
              window: model.window,
              visibleCount: model.visibleBeats.length,
              selectedVisible: model.visibleBeats.some((beat) => beat.blockId === "line_64"),
              selectedStatus: model.selectedBeat.status,
              expandedHtml,
              collapsedHtml,
              emptyHtml,
            }));
            """
        )

        self.assertTrue(payload["window"]["truncated"])
        self.assertEqual(payload["visibleCount"], 20)
        self.assertLessEqual(payload["window"]["firstNumber"], 64)
        self.assertGreaterEqual(payload["window"]["lastNumber"], 64)
        self.assertTrue(payload["selectedVisible"])
        self.assertEqual(payload["selectedStatus"], "blocker")
        self.assertIn("导演排练台", payload["expandedHtml"])
        self.assertIn('data-slot="scene-rehearsal-board"', payload["expandedHtml"])
        self.assertIn('data-state="expanded"', payload["expandedHtml"])
        self.assertIn('aria-expanded="true"', payload["expandedHtml"])
        self.assertIn('data-action="preview-story-location"', payload["expandedHtml"])
        self.assertIn('data-action="select-block"', payload["expandedHtml"])
        self.assertIn('aria-current="true"', payload["expandedHtml"])
        self.assertIn('data-lane="story"', payload["expandedHtml"])
        self.assertIn('data-lane="audio"', payload["expandedHtml"])
        self.assertIn("缺少关键素材", payload["expandedHtml"])
        self.assertNotIn('id="sceneRehearsalTracks" class="scene-rehearsal-expanded-content" hidden', payload["expandedHtml"])
        self.assertIn('data-state="collapsed"', payload["collapsedHtml"])
        self.assertIn('class="scene-rehearsal-expanded-content"\n          hidden', payload["collapsedHtml"])
        self.assertIn("场景有卡片后出现", payload["emptyHtml"])

    def test_rehearsal_board_is_wired_to_story_workspace_and_preview_actions(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")
        html = INDEX_PATH.read_text(encoding="utf-8")

        self.assertIn("const sceneRehearsalBoardTools = window.CanvasiaEditorSceneRehearsalBoard;", app_source)
        self.assertIn('action === "toggle-scene-rehearsal"', app_source)
        self.assertIn("function buildCurrentScenePresentationReport(scene)", app_source)
        self.assertIn("function renderCurrentSceneRehearsalBoard(scene)", app_source)
        self.assertIn("sceneRehearsalBoardTools.renderSceneRehearsalBoard", app_source)
        self.assertIn("sceneRehearsalBoardTools?.handleSceneRehearsalKeyboardNavigation", app_source)
        self.assertIn("refs.sceneRehearsalBoard.innerHTML", app_source)
        self.assertIn('action === "preview-story-location"', app_source)
        self.assertIn('id="sceneRehearsalBoard"', html)
        self.assertIn('<script src="./modules/scene_rehearsal_board.js"></script>', html)
        self.assertLess(
            html.index('<script src="./modules/scene_rehearsal_board.js"></script>'),
            html.index('<script type="module" src="./app.js"></script>'),
        )

    def test_rehearsal_beats_support_arrow_home_and_end_keyboard_navigation(self) -> None:
        payload = self.run_node(
            """
            const focusCalls = [];
            const preventCalls = [];
            const buttons = Array.from({ length: 3 }, (_, index) => ({
              disabled: false,
              focus: () => focusCalls.push(index),
              matches: (selector) => selector.includes('scene-rehearsal-beat'),
            }));
            const group = { querySelectorAll: () => buttons };
            buttons.forEach((button) => {
              button.closest = (selector) => selector === '[role="group"]' ? group : button;
            });
            const root = { contains: () => true };
            const run = (key, target) => tools.handleSceneRehearsalKeyboardNavigation({
              key,
              target,
              preventDefault: () => preventCalls.push(key),
            }, root);
            const results = [
              run("ArrowRight", buttons[1]),
              run("ArrowRight", buttons[2]),
              run("ArrowLeft", buttons[0]),
              run("Home", buttons[2]),
              run("End", buttons[0]),
              run("Enter", buttons[0]),
            ];
            process.stdout.write(JSON.stringify({ results, focusCalls, preventCalls }));
            """
        )

        self.assertEqual(payload["results"], [True, True, True, True, True, False])
        self.assertEqual(payload["focusCalls"], [2, 0, 2, 0, 2])
        self.assertEqual(payload["preventCalls"], ["ArrowRight", "ArrowRight", "ArrowLeft", "Home", "End"])


if __name__ == "__main__":
    unittest.main()
