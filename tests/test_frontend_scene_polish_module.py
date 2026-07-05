from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
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
            const cleanPlan = tools.buildScenePresentationPolishPlan({{ id: "clean", blocks: [
              {{ id: "line_ok", type: "dialogue", text: "短句", textSpeed: "fast" }},
              {{ id: "bg_ok", type: "background", transition: "crossfade", transitionDurationMs: 800 }},
              {{ id: "music_ok", type: "music_play", fadeInMs: 700, fadeOutMs: 900, volume: 65, loop: false, endMode: "after_block" }},
            ] }});
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


if __name__ == "__main__":
    unittest.main()
