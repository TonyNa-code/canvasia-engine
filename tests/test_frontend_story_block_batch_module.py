from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_batch.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"
INDEX_PATH = ROOT_DIR / "prototype_editor" / "index.html"


class FrontendStoryBlockBatchModuleTests(unittest.TestCase):
    def run_node(self, body: str) -> dict:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStoryBlockBatch;
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

    def test_selection_is_scene_ordered_and_supports_shift_ranges(self) -> None:
        payload = self.run_node(
            """
            const blocks = ["a", "b", "c", "d", "e"].map((id) => ({ id, type: "dialogue" }));
            const first = tools.updateStoryBlockSelection(blocks, [], "b", { checked: true });
            const ranged = tools.updateStoryBlockSelection(blocks, first.selectedIds, "d", {
              anchorId: first.anchorId,
              checked: true,
              range: true,
            });
            const withVisible = tools.selectVisibleStoryBlocks(blocks, ranged.selectedIds, ["a", "e"]);
            const pruned = tools.normalizeStoryBlockSelection(blocks, ["missing", "e", "b", "b"]);
            const model = tools.getStoryBlockSelectionModel(blocks, ["b", "c", "d"], ["a", "b", "c"]);
            process.stdout.write(JSON.stringify({ first, ranged, withVisible, pruned, model }));
            """
        )

        self.assertEqual(payload["first"]["selectedIds"], ["b"])
        self.assertEqual(payload["first"]["anchorId"], "b")
        self.assertEqual(payload["ranged"]["selectedIds"], ["b", "c", "d"])
        self.assertEqual(payload["ranged"]["anchorId"], "b")
        self.assertEqual(payload["withVisible"], ["a", "b", "c", "d", "e"])
        self.assertEqual(payload["pruned"], ["b", "e"])
        self.assertEqual(payload["model"]["selectedCount"], 3)
        self.assertEqual(payload["model"]["visibleSelectedCount"], 2)
        self.assertEqual(payload["model"]["hiddenSelectedCount"], 1)
        self.assertTrue(payload["model"]["contiguous"])

    def test_reorder_preserves_relative_order_and_repairs_invalid_music_ranges(self) -> None:
        payload = self.run_node(
            """
            const scattered = ["a", "b", "c", "d", "e"].map((id) => ({ id, type: "dialogue" }));
            const moved = tools.buildStoryBlockReorderPlan(scattered, ["b", "d"], "up");
            const musicBlocks = [
              { id: "music", type: "music_play", endMode: "after_block", endBlockId: "line_2" },
              { id: "line_1", type: "dialogue" },
              { id: "line_2", type: "dialogue" },
            ];
            const movedMusic = tools.buildStoryBlockReorderPlan(musicBlocks, ["music"], "end");
            process.stdout.write(JSON.stringify({
              scatteredSource: scattered.map((block) => block.id),
              moved: moved.blocks.map((block) => block.id),
              selected: moved.selectedIds,
              musicOrder: movedMusic.blocks.map((block) => block.id),
              music: movedMusic.blocks[2],
              repairs: movedMusic.repairCount,
            }));
            """
        )

        self.assertEqual(payload["scatteredSource"], ["a", "b", "c", "d", "e"])
        self.assertEqual(payload["moved"], ["b", "a", "d", "c", "e"])
        self.assertEqual(payload["selected"], ["b", "d"])
        self.assertEqual(payload["musicOrder"], ["line_1", "line_2", "music"])
        self.assertEqual(payload["music"]["endMode"], "until_next_music")
        self.assertEqual(payload["music"]["endBlockId"], "")
        self.assertEqual(payload["repairs"], 1)

    def test_duplicate_places_a_group_after_selection_and_remaps_internal_range(self) -> None:
        payload = self.run_node(
            """
            const blocks = [
              { id: "music", type: "music_play", endMode: "after_block", endBlockId: "line_2" },
              { id: "line_1", type: "dialogue" },
              { id: "line_2", type: "dialogue" },
              { id: "tail", type: "narration" },
            ];
            let nextId = 1;
            const plan = tools.buildStoryBlockDuplicatePlan(blocks, ["music", "line_2"], {
              duplicateBlock: (block) => ({ ...block, id: `copy_${nextId++}` }),
            });
            const externalTargetPlan = tools.buildStoryBlockDuplicatePlan(blocks, ["music", "tail"], {
              duplicateBlock: (block) => ({ ...block, id: `external_${nextId++}` }),
            });
            process.stdout.write(JSON.stringify({
              source: blocks,
              order: plan.blocks.map((block) => block.id),
              copies: plan.blocks.filter((block) => block.id.startsWith("copy_")),
              selected: plan.selectedIds,
              focus: plan.selectedBlockId,
              previewIndex: plan.previewIndex,
              repairedExternalMusic: externalTargetPlan.blocks.find((block) => block.id.startsWith("external_")),
              externalRepairCount: externalTargetPlan.repairCount,
            }));
            """
        )

        self.assertEqual(payload["order"], ["music", "line_1", "line_2", "copy_1", "copy_2", "tail"])
        self.assertEqual(payload["copies"][0]["endBlockId"], "copy_2")
        self.assertEqual(payload["selected"], ["copy_1", "copy_2"])
        self.assertEqual(payload["focus"], "copy_1")
        self.assertEqual(payload["previewIndex"], 3)
        self.assertEqual(payload["source"][0]["endBlockId"], "line_2")
        self.assertEqual(payload["repairedExternalMusic"]["endMode"], "until_next_music")
        self.assertEqual(payload["repairedExternalMusic"]["endBlockId"], "")
        self.assertEqual(payload["externalRepairCount"], 1)

    def test_delete_repairs_dangling_ranges_and_selects_a_nearby_survivor(self) -> None:
        payload = self.run_node(
            """
            const blocks = [
              { id: "music", type: "music_play", endMode: "after_block", endBlockId: "line_2" },
              { id: "line_1", type: "dialogue" },
              { id: "line_2", type: "dialogue" },
              { id: "tail", type: "narration" },
            ];
            const plan = tools.buildStoryBlockDeletePlan(blocks, ["line_2"]);
            const deleteAll = tools.buildStoryBlockDeletePlan(blocks, blocks.map((block) => block.id));
            process.stdout.write(JSON.stringify({ plan, deleteAll }));
            """
        )

        self.assertEqual([block["id"] for block in payload["plan"]["blocks"]], ["music", "line_1", "tail"])
        self.assertEqual(payload["plan"]["blocks"][0]["endMode"], "until_next_music")
        self.assertEqual(payload["plan"]["repairCount"], 1)
        self.assertEqual(payload["plan"]["selectedBlockId"], "tail")
        self.assertEqual(payload["plan"]["previewIndex"], 2)
        self.assertEqual(payload["deleteAll"]["blocks"], [])
        self.assertEqual(payload["deleteAll"]["selectedBlockId"], "")

    def test_toolbar_is_accessible_and_wired_into_the_editor_contract(self) -> None:
        payload = self.run_node(
            """
            const scene = {
              id: "scene_1",
              blocks: [
                { id: "a", type: "dialogue" },
                { id: "b", type: "narration" },
                { id: "c", type: "choice" },
              ],
            };
            const emptyHtml = tools.renderStoryBlockBatchToolbar(scene, scene.blocks, []);
            const selectedHtml = tools.renderStoryBlockBatchToolbar(scene, scene.blocks.slice(0, 2), ["a", "c"]);
            process.stdout.write(JSON.stringify({ emptyHtml, selectedHtml, keys: Object.keys(tools).sort() }));
            """
        )
        app_source = APP_PATH.read_text(encoding="utf-8")
        html = INDEX_PATH.read_text(encoding="utf-8")

        self.assertIn("buildStoryBlockReorderPlan", payload["keys"])
        self.assertIn("renderStoryBlockBatchToolbar", payload["keys"])
        self.assertIn('data-slot="story-block-batch-toolbar"', payload["emptyHtml"])
        self.assertIn('aria-label="剧情卡片剪辑选区"', payload["emptyHtml"])
        self.assertIn('data-action="select-all-visible-story-blocks"', payload["emptyHtml"])
        self.assertIn('data-action="duplicate-story-block-selection"', payload["selectedHtml"])
        self.assertIn('data-action="delete-story-block-selection"', payload["selectedHtml"])
        self.assertIn("其中 1 张在筛选外", payload["selectedHtml"])
        self.assertIn("const storyBlockBatchTools = window.CanvasiaEditorStoryBlockBatch;", app_source)
        self.assertIn("const storyBlockBatchController = storyBlockBatchTools.createStoryBlockBatchController", app_source)
        self.assertIn("flushPendingChanges: () => flushPendingStoryChanges()", app_source)
        self.assertIn('id="storyBlockBatchToolbar"', html)
        self.assertIn('<script src="./modules/story_block_batch.js"></script>', html)
        self.assertLess(
            html.index('<script src="./modules/story_block_batch.js"></script>'),
            html.index('<script type="module" src="./app.js"></script>'),
        )

    def test_controller_coordinates_selection_save_and_focused_card_operations(self) -> None:
        payload = self.run_node(
            """
            (async () => {
              let scene = {
                id: "scene_1",
                blocks: ["a", "b", "c", "d"].map((id) => ({ id, type: "dialogue", text: id })),
              };
              let selectedIds = [];
              let anchorId = "";
              let focusedBlockId = "a";
              let busy = false;
              let copyNumber = 1;
              const saves = [];
              const controller = tools.createStoryBlockBatchController({
                getScene: () => scene,
                getVisibleBlocks: () => scene.blocks,
                getSelectedIds: () => selectedIds,
                getAnchorId: () => anchorId,
                getFocusedBlockId: () => focusedBlockId,
                setSelection: (ids, anchor) => { selectedIds = ids; anchorId = anchor; },
                getBusy: () => busy,
                setBusy: (value) => { busy = value; },
                flushPendingChanges: async () => true,
                persistScene: async (nextScene, options) => {
                  scene = nextScene;
                  focusedBlockId = options.selectedBlockId;
                  saves.push({ order: nextScene.blocks.map((block) => block.id), options });
                  return true;
                },
                duplicateBlockForScene: (_scene, block) => ({ ...block, id: `copy_${copyNumber++}` }),
                showConfirm: async () => true,
              });
              controller.toggle("b");
              controller.toggle("d", { range: true });
              await controller.reorder("up");
              await controller.moveFocused(-1);
              await controller.duplicateFocused();
              process.stdout.write(JSON.stringify({
                selectedIds,
                anchorId,
                focusedBlockId,
                busy,
                saves,
                finalOrder: scene.blocks.map((block) => block.id),
              }));
            })().catch((error) => {
              console.error(error);
              process.exitCode = 1;
            });
            """
        )

        self.assertEqual(payload["selectedIds"], ["b", "c", "d"])
        self.assertEqual(payload["anchorId"], "d")
        self.assertFalse(payload["busy"])
        self.assertEqual(payload["saves"][0]["order"], ["b", "c", "d", "a"])
        self.assertEqual(payload["saves"][0]["options"]["storyBlockCheckedIds"], ["b", "c", "d"])
        self.assertEqual(payload["saves"][1]["order"], ["b", "c", "a", "d"])
        self.assertEqual(payload["finalOrder"], ["b", "c", "a", "copy_1", "d"])
        self.assertEqual(payload["focusedBlockId"], "copy_1")


if __name__ == "__main__":
    unittest.main()
