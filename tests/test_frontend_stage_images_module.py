from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "stage_images.js"


class FrontendStageImagesModuleTests(unittest.TestCase):
    def test_stage_image_state_presets_updates_and_hides_are_stable(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStageImages;
            const clamped = tools.normalizeStageImageState({{
              layerId: "  hero prop  ",
              assetId: "asset_prop",
              plane: "unknown",
              position: "offstage",
              transform: {{
                offsetX: -999,
                offsetY: 999,
                width: 999,
                opacity: -5,
                rotation: 999,
                layer: 99,
                flipX: "yes",
              }},
            }});
            const preset = tools.applyStageImagePreset({{
              layerId: "letter",
              assetId: "letter_png",
            }}, "cut_in");
            const first = tools.applyStageImageBlock([], {{
              type: "stage_image",
              action: "show",
              layerId: "foreground",
              assetId: "leaves",
              plane: "front",
              position: "right",
              transform: {{ width: 92, offsetY: 16, rotation: 8, layer: 3, flipX: true }},
              durationMs: 600,
              easing: "ease_in_out",
            }});
            const second = tools.applyStageImageBlock(first.visibleImages, {{
              action: "update",
              layerId: "foreground",
              transform: {{ width: 44, opacity: 70, layer: -2 }},
            }});
            const ordered = tools.sortStageImages([
              {{ layerId: "front-high", plane: "front", transform: {{ layer: 8 }} }},
              {{ layerId: "back", plane: "back", transform: {{ layer: 10 }} }},
              {{ layerId: "front-low", plane: "front", transform: {{ layer: -4 }} }},
            ]);
            const hidden = tools.applyStageImageBlock(second.visibleImages, {{
              action: "hide",
              layerId: "foreground",
              durationMs: 240,
            }});
            const editorHtml = tools.renderStageImageEditor({{
              action: "show",
              layerId: "letter",
              assetId: "letter_png",
              plane: "front",
              position: "center",
              transform: {{ width: 58, opacity: 90 }},
              durationMs: 700,
              easing: "ease_in_out",
            }}, {{
              assets: [{{ id: "letter_png", name: "手写信", type: "cg" }}],
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              clamped,
              preset,
              first,
              second,
              ordered: ordered.map((item) => item.layerId),
              hidden,
              summary: tools.getStageImageSummary({{
                action: "show",
                layerId: "letter",
                assetId: "letter_png",
                plane: "front",
                position: "center",
              }}, "手写信"),
              duration: tools.getSafeStageImageDurationMs(99999),
              style: tools.getStageImageStyle(preset),
              motionStyle: tools.getStageImageMotionStyle(second.event),
              editorHtml,
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
        self.assertIn("applyStageImageBlock", payload["keys"])
        self.assertEqual(payload["clamped"]["layerId"], "hero_prop")
        self.assertEqual(payload["clamped"]["plane"], "front")
        self.assertEqual(payload["clamped"]["position"], "center")
        self.assertEqual(payload["clamped"]["transform"]["offsetX"], -80)
        self.assertEqual(payload["clamped"]["transform"]["offsetY"], 70)
        self.assertEqual(payload["clamped"]["transform"]["width"], 180)
        self.assertEqual(payload["clamped"]["transform"]["opacity"], 0)
        self.assertEqual(payload["clamped"]["transform"]["rotation"], 180)
        self.assertEqual(payload["clamped"]["transform"]["layer"], 20)
        self.assertTrue(payload["clamped"]["transform"]["flipX"])
        self.assertEqual(payload["preset"]["transform"]["width"], 58)
        self.assertEqual(payload["first"]["event"]["mode"], "show")
        self.assertEqual(payload["second"]["event"]["mode"], "move")
        self.assertEqual(payload["second"]["visibleImages"][0]["assetId"], "leaves")
        self.assertEqual(payload["second"]["visibleImages"][0]["transform"]["width"], 44)
        self.assertEqual(payload["second"]["visibleImages"][0]["transform"]["offsetY"], 16)
        self.assertEqual(payload["second"]["visibleImages"][0]["transform"]["rotation"], 8)
        self.assertTrue(payload["second"]["visibleImages"][0]["transform"]["flipX"])
        self.assertEqual(payload["ordered"], ["back", "front-low", "front-high"])
        self.assertEqual(payload["hidden"]["visibleImages"], [])
        self.assertEqual(payload["hidden"]["event"]["mode"], "hide")
        self.assertIn("手写信", payload["summary"])
        self.assertEqual(payload["duration"], 10000)
        self.assertIn("--stage-image-width:58%", payload["style"])
        self.assertIn("--stage-image-motion-ms:520ms", payload["motionStyle"])
        self.assertIn("编辑舞台贴图", payload["editorHtml"])
        self.assertIn('data-action="apply-stage-image-preset"', payload["editorHtml"])
        self.assertIn('value="letter_png" selected', payload["editorHtml"])


if __name__ == "__main__":
    unittest.main()
