from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def read_source(relative_path: str) -> str:
    return (ROOT_DIR / relative_path).read_text(encoding="utf-8")


class StageImageContractTests(unittest.TestCase):
    def test_editor_web_runtime_and_export_packaging_share_stage_image_contract(self) -> None:
        run_editor = read_source("run_editor.py")
        editor_app = read_source("prototype_editor/app.js")
        editor_module = read_source("prototype_editor/modules/stage_images.js")
        player = read_source("export_player_template/player.js")
        web_module = read_source("export_player_template/runtime_stage_images.js")
        player_html = read_source("export_player_template/index.html")
        native_player = read_source("native_runtime/runtime_player.py")
        native_module = read_source("native_runtime/runtime_stage_images.py")

        self.assertIn('type: "stage_image"', editor_app)
        self.assertIn('case "stage_image"', editor_app)
        self.assertIn("applyStageImageBlock", editor_module)
        self.assertIn('from "./runtime_stage_images.js"', player)
        self.assertIn('case "stage_image"', player)
        self.assertIn("buildStageImageRenderItems", web_module)
        self.assertIn('id="stageImageBackLayer"', player_html)
        self.assertIn('id="stageImageFrontLayer"', player_html)
        self.assertIn('"runtime_stage_images.js"', run_editor)
        self.assertIn('"playerRuntimeStageImages": "runtime_stage_images.js"', run_editor)
        self.assertEqual(run_editor.count('"appRuntimeStageImages": "app/runtime_stage_images.js"'), 3)
        self.assertIn('NATIVE_RUNTIME_STAGE_IMAGES_NAME = "runtime_stage_images.py"', run_editor)
        self.assertIn("NATIVE_RUNTIME_STAGE_IMAGES_SOURCE, NATIVE_RUNTIME_STAGE_IMAGES_NAME", run_editor)
        self.assertIn('"runtimeStageImagesModule": runtime_files["runtimeStageImagesModuleName"]', run_editor)
        self.assertIn("apply_native_stage_image_block", native_player)
        self.assertIn('block_type == "stage_image"', native_player)
        self.assertIn("get_native_stage_image_render_pose", native_module)

        for token in ("offsetX", "offsetY", "width", "opacity", "rotation", "layer", "flipX"):
            self.assertIn(token, editor_module)
            self.assertIn(token, web_module)
            self.assertIn(token, native_module)


if __name__ == "__main__":
    unittest.main()
