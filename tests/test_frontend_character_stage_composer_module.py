from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_DIR = ROOT_DIR / "prototype_editor"
MODULE_PATH = EDITOR_DIR / "modules" / "character_stage_composer.js"
VISUAL_EFFECTS_PATH = EDITOR_DIR / "modules" / "visual_effects.js"
APP_PATH = EDITOR_DIR / "app.js"
INDEX_PATH = EDITOR_DIR / "index.html"
MODULE_GUARD_PATH = EDITOR_DIR / "modules" / "module_guard.js"
STYLES_PATH = EDITOR_DIR / "styles.css"


class FrontendCharacterStageComposerModuleTests(unittest.TestCase):
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
            const tools = context.window.CanvasiaEditorCharacterStageComposer;
            const options = {{
              getSafeCharacterStage: visual.getSafeCharacterStage,
              getSafePosition: visual.getSafePosition,
              getPositionLabel: visual.getPositionLabel,
              getCharacterStageSummary: visual.getCharacterStageSummary,
              getCharacterStageStyle: visual.getCharacterStageStyle,
              getMatchingBuiltInPresetId: visual.getMatchingCharacterStagePresetId,
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

    def test_preset_ids_remain_stable_and_save_delete_plans_are_deterministic(self) -> None:
        payload = self.run_node(
            """
            const normalized = tools.normalizeCharacterStagePresets([
              { id: "stage_close", name: "近景", position: "left", stage: { scale: 140 } },
              { id: "stage_close", name: "重复近景", position: "bad", stage: { scale: 999, flipX: "yes" } },
              { id: "不安全 ID", name: "中文构图", stage: { opacity: -4 } },
            ], options);
            const update = tools.buildCharacterStagePresetSavePlan({
              name: "近景更新",
              selectedPresetId: "stage_close",
              position: "right",
              stage: { offsetX: 10, scale: 132 },
              currentPresets: normalized,
            }, options);
            const add = tools.buildCharacterStagePresetSavePlan({
              name: "close",
              position: "center",
              stage: { scale: 110 },
              currentPresets: update.nextPresets,
            }, options);
            const remove = tools.buildCharacterStagePresetDeletePlan(add.nextPresets, add.targetId, options);
            process.stdout.write(JSON.stringify({ normalized, update, add, remove }));
            """
        )

        self.assertEqual([item["id"] for item in payload["normalized"]], ["stage_close", "stage_close_02", "id"])
        self.assertEqual(payload["normalized"][1]["position"], "center")
        self.assertEqual(payload["normalized"][1]["stage"]["scale"], 220)
        self.assertTrue(payload["normalized"][1]["stage"]["flipX"])
        self.assertEqual(payload["normalized"][2]["stage"]["opacity"], 0)
        self.assertTrue(payload["update"]["isUpdate"])
        self.assertEqual(payload["update"]["targetId"], "stage_close")
        self.assertEqual(payload["update"]["nextPresets"][0]["position"], "right")
        self.assertFalse(payload["add"]["isUpdate"])
        self.assertEqual(payload["add"]["targetId"], "stage_close_03")
        self.assertTrue(payload["remove"]["ok"])
        self.assertEqual(len(payload["remove"]["nextPresets"]), 3)

    def test_drag_keyboard_and_wheel_math_clamps_to_runtime_safe_values(self) -> None:
        payload = self.run_node(
            """
            const dragged = tools.buildDraggedCharacterStage(
              { offsetX: 50, offsetY: -40, scale: 100, opacity: 100, layer: 0 },
              { deltaX: 50, deltaY: -50, referenceWidth: 100, referenceHeight: 100 },
              options
            );
            const precise = tools.buildDraggedCharacterStage(
              { offsetX: 0, offsetY: 0 },
              { deltaX: 10, deltaY: 10, referenceWidth: 100, referenceHeight: 100, precise: true },
              options
            );
            process.stdout.write(JSON.stringify({
              dragged,
              precise,
              keyboard: [
                tools.getCharacterStageKeyboardDelta({ code: "ArrowLeft", shiftKey: false }),
                tools.getCharacterStageKeyboardDelta({ code: "Equal", shiftKey: true }),
                tools.getCharacterStageKeyboardDelta({ code: "BracketRight", shiftKey: false }),
              ],
              wheel: [
                tools.getCharacterStageWheelDelta({ deltaY: -10, shiftKey: false }),
                tools.getCharacterStageWheelDelta({ deltaY: 10, shiftKey: true }),
              ],
            }));
            """
        )

        self.assertEqual(payload["dragged"]["offsetX"], 60)
        self.assertEqual(payload["dragged"]["offsetY"], -45)
        self.assertEqual(payload["precise"]["offsetX"], 4)
        self.assertEqual(payload["precise"]["offsetY"], 4)
        self.assertEqual(payload["keyboard"], [{"offsetX": -2}, {"scale": 12}, {"layer": 1}])
        self.assertEqual(payload["wheel"], [{"scale": 4}, {"scale": -12}])

    def test_rendered_composer_uses_real_sprite_and_exposes_accessible_controls(self) -> None:
        payload = self.run_node(
            """
            const html = tools.renderCharacterStageControls(
              { offsetX: 8, offsetY: -4, scale: 118, opacity: 90, layer: 2, flipX: true },
              {
                ...options,
                position: "right",
                spriteUrl: "/assets/heroine.png",
                spriteLabel: "女主角",
                backdropStyle: "background: #123;",
                builtInPresets: visual.getCharacterStagePresetEntries(),
                adjustments: visual.getCharacterStageAdjustmentEntries(),
                customPresets: [
                  { id: "stage_dialogue", name: "双人对话", position: "left", stage: { scale: 96 } },
                ],
              }
            );
            process.stdout.write(JSON.stringify({ html, keys: Object.keys(tools).sort() }));
            """
        )
        html = payload["html"]

        self.assertIn("createCharacterStageComposerController", payload["keys"])
        self.assertIn('data-character-stage-preview', html)
        self.assertIn('src="/assets/heroine.png"', html)
        self.assertIn('aria-grabbed="false"', html)
        self.assertIn("滚轮调大小", html)
        self.assertIn('data-action="apply-character-stage-preset"', html)
        self.assertIn('data-action="apply-custom-character-stage-preset"', html)
        self.assertIn('data-action="save-character-stage-preset"', html)
        self.assertIn('data-action="delete-character-stage-preset"', html)
        self.assertIn('id="editorCharacterFlipX"', html)
        self.assertIn("水平镜像立绘", html)

    def test_editor_entrypoint_guard_styles_and_handlers_share_one_module_contract(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")
        index_source = INDEX_PATH.read_text(encoding="utf-8")
        guard_source = MODULE_GUARD_PATH.read_text(encoding="utf-8")
        styles_source = STYLES_PATH.read_text(encoding="utf-8")

        self.assertIn("const characterStageComposerTools = window.CanvasiaEditorCharacterStageComposer;", app_source)
        self.assertIn("characterStageComposerTools.createCharacterStageComposerController", app_source)
        self.assertIn('action === "save-character-stage-preset"', app_source)
        self.assertIn('action === "delete-character-stage-preset"', app_source)
        self.assertIn("characterStagePresets: plan.nextPresets", app_source)
        self.assertIn('<script src="./modules/character_stage_composer.js"></script>', index_source)
        self.assertLess(
            index_source.index('<script src="./modules/character_stage_composer.js"></script>'),
            index_source.index('<script type="module" src="./app.js"></script>'),
        )
        self.assertIn('globalName: "CanvasiaEditorCharacterStageComposer"', guard_source)
        self.assertIn(".stage-composer-monitor", styles_source)
        self.assertIn('html[data-ui-theme="light"] .character-stage-controls', styles_source)


if __name__ == "__main__":
    unittest.main()
