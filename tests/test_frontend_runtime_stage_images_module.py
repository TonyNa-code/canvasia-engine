from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_stage_images.js"


class FrontendRuntimeStageImagesModuleTests(unittest.TestCase):
    def test_runtime_stage_images_preserve_layers_and_transition_ghosts(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};
            const shown = tools.applyStageImageBlock([], {{
              action: "show", layerId: "letter", assetId: "letter_png", plane: "front",
              position: "center", transform: {{ width: 64, opacity: 92, rotation: 11, layer: 3, flipX: true }},
              durationMs: 700, easing: "spring",
            }});
            const moved = tools.applyStageImageBlock(shown.visibleImages, {{
              action: "update", layerId: "letter", position: "right",
              transform: {{ width: 40, offsetX: -12, opacity: 80, layer: -2 }},
              durationMs: 900, easing: "ease_in_out",
            }});
            const hidden = tools.applyStageImageBlock(moved.visibleImages, {{
              action: "hide", layerId: "letter", durationMs: 300,
            }});
            process.stdout.write(JSON.stringify({{
              shown,
              moved,
              hidden,
              moveItems: tools.buildStageImageRenderItems(moved.visibleImages, moved.event, "front"),
              hideItems: tools.buildStageImageRenderItems(hidden.visibleImages, hidden.event, "front"),
              clamped: tools.getSafeStageImageTransform({{ width: 500, opacity: -1, offsetX: -999 }}),
            }}));
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["shown"]["event"]["mode"], "show")
        self.assertEqual(payload["moved"]["event"]["mode"], "move")
        self.assertEqual(payload["moved"]["visibleImages"][0]["assetId"], "letter_png")
        self.assertEqual(payload["moved"]["visibleImages"][0]["transform"]["rotation"], 11)
        self.assertTrue(payload["moved"]["visibleImages"][0]["transform"]["flipX"])
        self.assertEqual(payload["moveItems"][0]["eventMode"], "move")
        self.assertIn("--stage-image-from-position-x:50%", payload["moveItems"][0]["style"])
        self.assertEqual(payload["hidden"]["visibleImages"], [])
        self.assertEqual(payload["hideItems"][0]["ghostMode"], "hide")
        self.assertEqual(payload["clamped"]["width"], 180)
        self.assertEqual(payload["clamped"]["opacity"], 0)
        self.assertEqual(payload["clamped"]["offsetX"], -80)


if __name__ == "__main__":
    unittest.main()
