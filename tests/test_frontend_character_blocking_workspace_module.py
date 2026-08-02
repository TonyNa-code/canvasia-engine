from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_DIR = ROOT_DIR / "prototype_editor"
MODULE_PATH = EDITOR_DIR / "modules" / "character_blocking_workspace.js"
VISUAL_EFFECTS_PATH = EDITOR_DIR / "modules" / "visual_effects.js"
APP_PATH = EDITOR_DIR / "app.js"
INDEX_PATH = EDITOR_DIR / "index.html"
MODULE_GUARD_PATH = EDITOR_DIR / "modules" / "module_guard.js"
STYLES_PATH = EDITOR_DIR / "styles.css"


class FrontendCharacterBlockingWorkspaceModuleTests(unittest.TestCase):
    def run_node(self, body: str) -> dict:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(VISUAL_EFFECTS_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const visual = context.window.CanvasiaEditorVisualEffects;
            const tools = context.window.CanvasiaEditorCharacterBlockingWorkspace;
            const visuals = {{
              alice: {{ characterName: "Alice", expressionName: "Smile", spriteUrl: "/alice.png", defaultPosition: "left" }},
              bob: {{ characterName: "Bob", expressionName: "Calm", spriteUrl: "/bob.png", defaultPosition: "right" }},
              carol: {{ characterName: "Carol", expressionName: "Default", spriteUrl: "", defaultPosition: "center" }},
            }};
            const options = {{
              getSafeCharacterStage: visual.getSafeCharacterStage,
              getSafePosition: visual.getSafePosition,
              getCharacterVisual: (characterId, expressionId) => ({{
                ...(visuals[characterId] || {{ characterName: characterId }}),
                characterId,
                expressionId,
              }}),
            }};
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

    def test_model_reconstructs_visible_cast_and_detects_overlap(self) -> None:
        payload = self.run_node(
            """
            const scene = {
              id: "scene_1",
              name: "Classroom",
              blocks: [
                { id: "show_a", type: "character_show", characterId: "alice", expressionId: "smile", position: "left", stage: { scale: 126 } },
                { id: "show_b", type: "character_show", characterId: "bob", expressionId: "calm", position: "left", stage: { offsetX: 2, scale: 120 } },
                { id: "line_a", type: "dialogue", speakerId: "alice", expressionId: "shy", text: "Hello" },
              ],
            };
            const model = tools.buildCharacterBlockingModel(scene, "show_b", options);
            process.stdout.write(JSON.stringify(model));
            """
        )

        self.assertEqual(payload["summary"]["visibleCount"], 2)
        self.assertEqual(payload["summary"]["controllableCount"], 2)
        self.assertEqual(payload["selectedCharacterId"], "bob")
        self.assertEqual(payload["characters"][0]["controlBlockId"], "show_a")
        self.assertEqual(payload["characters"][1]["spriteUrl"], "/bob.png")
        self.assertGreaterEqual(payload["summary"]["overlapCount"], 1)
        self.assertEqual(payload["issues"][0]["code"], "cast_overlap")

    def test_duo_and_focus_formations_patch_multiple_cards_without_mutating_source(self) -> None:
        payload = self.run_node(
            """
            const scene = {
              id: "scene_1",
              blocks: [
                { id: "show_a", type: "character_show", characterId: "alice", position: "center", transition: "fade", stage: { scale: 90, flipX: true } },
                { id: "show_b", type: "character_show", characterId: "bob", position: "center", transition: "rise", stage: { scale: 96 } },
              ],
            };
            const duo = tools.buildCharacterBlockingFormationPlan(scene, "show_b", "dialogue_duo", options);
            const focus = tools.buildCharacterBlockingFormationPlan(scene, "show_b", "focus_selected", options);
            process.stdout.write(JSON.stringify({ scene, duo, focus }));
            """
        )

        self.assertTrue(payload["duo"]["ok"])
        self.assertEqual(len(payload["duo"]["patches"]), 2)
        duo_blocks = payload["duo"]["scene"]["blocks"]
        self.assertEqual([block["position"] for block in duo_blocks], ["left", "right"])
        self.assertEqual([block["stage"]["scale"] for block in duo_blocks], [112, 112])
        self.assertTrue(duo_blocks[0]["stage"]["flipX"])
        self.assertEqual([block["transition"] for block in duo_blocks], ["fade", "rise"])
        self.assertEqual([block["position"] for block in payload["scene"]["blocks"]], ["center", "center"])

        focus_blocks = payload["focus"]["scene"]["blocks"]
        self.assertEqual(focus_blocks[1]["position"], "center")
        self.assertEqual(focus_blocks[1]["stage"]["scale"], 126)
        self.assertEqual(focus_blocks[1]["stage"]["layer"], 5)
        self.assertEqual(focus_blocks[0]["stage"]["opacity"], 84)

    def test_implicit_cast_is_reported_and_skipped_by_safe_formation_plan(self) -> None:
        payload = self.run_node(
            """
            const scene = {
              id: "scene_implicit",
              blocks: [
                { id: "show_a", type: "character_show", characterId: "alice", position: "left" },
                { id: "show_b", type: "character_show", characterId: "bob", position: "right" },
                { id: "line_c", type: "dialogue", speakerId: "carol", text: "I appeared automatically" },
              ],
            };
            const model = tools.buildCharacterBlockingModel(scene, "line_c", options);
            const plan = tools.buildCharacterBlockingFormationPlan(scene, "line_c", "balanced", options);
            const focus = tools.getFormationEntries(model).find((entry) => entry.id === "focus_selected");
            process.stdout.write(JSON.stringify({ model, plan, focus }));
            """
        )

        self.assertEqual(payload["model"]["summary"]["visibleCount"], 3)
        self.assertEqual(payload["model"]["summary"]["controllableCount"], 2)
        self.assertEqual(payload["model"]["summary"]["implicitCount"], 1)
        self.assertTrue(any(issue["code"] == "cast_implicit" for issue in payload["model"]["issues"]))
        self.assertTrue(payload["plan"]["ok"])
        self.assertEqual(len(payload["plan"]["patches"]), 2)
        self.assertEqual(payload["plan"]["skippedCount"], 1)
        self.assertFalse(payload["focus"]["enabled"])
        self.assertIn("明确走位卡", payload["focus"]["reason"])

    def test_controller_blocks_duplicate_formation_saves_while_first_is_pending(self) -> None:
        payload = self.run_node(
            """
            (async () => {
              const scene = {
                id: "scene_1",
                blocks: [
                  { id: "show_a", type: "character_show", characterId: "alice", position: "center" },
                  { id: "show_b", type: "character_show", characterId: "bob", position: "center" },
                ],
              };
              let releaseFlush;
              const flushGate = new Promise((resolve) => { releaseFlush = resolve; });
              let saveCount = 0;
              const toasts = [];
              const controller = tools.createCharacterBlockingController({
                ...options,
                getScene: () => scene,
                getSelectedBlockId: () => "show_b",
                flushPendingChanges: () => flushGate,
                confirm: async () => true,
                persistScene: async () => { saveCount += 1; return true; },
                showToast: (message) => toasts.push(message),
              });
              const firstPromise = controller.applyFormation("dialogue_duo");
              const secondResult = await controller.applyFormation("dialogue_duo");
              releaseFlush(true);
              const firstResult = await firstPromise;
              process.stdout.write(JSON.stringify({ firstResult, secondResult, saveCount, toasts }));
            })().catch((error) => {
              process.stderr.write(String(error?.stack || error));
              process.exitCode = 1;
            });
            """
        )

        self.assertTrue(payload["firstResult"])
        self.assertFalse(payload["secondResult"])
        self.assertEqual(payload["saveCount"], 1)
        self.assertTrue(any("正在保存" in message for message in payload["toasts"]))

    def test_rendered_workspace_exposes_cast_navigation_and_formation_actions(self) -> None:
        payload = self.run_node(
            """
            const scene = {
              id: "scene_1",
              blocks: [
                { id: "show_a", type: "character_show", characterId: "alice", position: "left" },
                { id: "show_b", type: "character_show", characterId: "bob", position: "right" },
              ],
            };
            const model = tools.buildCharacterBlockingModel(scene, "show_b", options);
            const sprites = tools.renderCharacterBlockingSprites(model, {
              getCharacterStageStyle: visual.getCharacterStageStyle,
            });
            const panel = tools.renderCharacterBlockingWorkspace(model);
            process.stdout.write(JSON.stringify({ sprites, panel, keys: Object.keys(tools).sort() }));
            """
        )

        self.assertIn("createCharacterBlockingController", payload["keys"])
        self.assertIn('src="/alice.png"', payload["sprites"])
        self.assertNotIn('src="/bob.png"', payload["sprites"])
        self.assertIn('data-action="select-block"', payload["sprites"])
        self.assertIn("多人走位台", payload["panel"])
        self.assertIn('data-action="apply-character-blocking-formation"', payload["panel"])
        self.assertIn('data-character-blocking-formation="dialogue_duo"', payload["panel"])
        self.assertIn("<b>2</b> 人在场", payload["panel"])

    def test_entrypoint_guard_styles_and_app_handler_share_one_contract(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")
        index_source = INDEX_PATH.read_text(encoding="utf-8")
        guard_source = MODULE_GUARD_PATH.read_text(encoding="utf-8")
        styles_source = STYLES_PATH.read_text(encoding="utf-8")

        self.assertIn("const characterBlockingTools = window.CanvasiaEditorCharacterBlockingWorkspace;", app_source)
        self.assertIn("characterBlockingTools.createCharacterBlockingController", app_source)
        self.assertIn('action === "apply-character-blocking-formation"', app_source)
        self.assertIn('<script src="./modules/character_blocking_workspace.js"></script>', index_source)
        self.assertLess(
            index_source.index('<script src="./modules/character_blocking_workspace.js"></script>'),
            index_source.index('<script src="./modules/character_stage_composer.js"></script>'),
        )
        self.assertIn('globalName: "CanvasiaEditorCharacterBlockingWorkspace"', guard_source)
        self.assertIn(".stage-blocking-workspace", styles_source)
        self.assertIn(".stage-blocking-formation", styles_source)


if __name__ == "__main__":
    unittest.main()
