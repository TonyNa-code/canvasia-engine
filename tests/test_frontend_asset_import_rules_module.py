from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "asset_import_rules.js"


class FrontendAssetImportRulesModuleTests(unittest.TestCase):
    def test_asset_import_rules_cover_core_and_advanced_asset_types(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorAssetImportRules;

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              replaceAccepts: {{
                background: tools.getAssetReplaceAccept("background"),
                voice: tools.getAssetReplaceAccept("voice"),
                video: tools.getAssetReplaceAccept("video"),
                font: tools.getAssetReplaceAccept("font"),
                live2d: tools.getAssetReplaceAccept("live2d"),
                model3d: tools.getAssetReplaceAccept("model3d"),
                scene3d: tools.getAssetReplaceAccept("scene3d"),
                unknown: tools.getAssetReplaceAccept("unknown"),
              }},
              formatLabels: {{
                video: tools.getAssetReplaceFormatLabel("video"),
                live2d: tools.getAssetReplaceFormatLabel("live2d"),
                model3d: tools.getAssetReplaceFormatLabel("model3d"),
                unknown: tools.getAssetReplaceFormatLabel("unknown"),
                customFallback: tools.getAssetReplaceFormatLabel("unknown", "自定义兜底"),
              }},
              smartAccept: tools.ASSET_SMART_IMPORT_ACCEPT,
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
        self.assertIn("ASSET_REPLACE_ACCEPTS", payload["keys"])
        self.assertEqual(payload["replaceAccepts"]["background"], "image/*,.png,.jpg,.jpeg,.webp,.gif,.avif")
        self.assertIn(".flac", payload["replaceAccepts"]["voice"])
        self.assertIn(".mp4", payload["replaceAccepts"]["video"])
        self.assertIn(".ttf", payload["replaceAccepts"]["font"])
        self.assertIn(".model3.json", payload["replaceAccepts"]["live2d"])
        self.assertIn(".glb", payload["replaceAccepts"]["model3d"])
        self.assertIn(".vrm", payload["replaceAccepts"]["scene3d"])
        self.assertEqual(payload["replaceAccepts"]["unknown"], "")
        self.assertEqual(payload["formatLabels"]["video"], "MP4 / WebM / MOV / M4V")
        self.assertIn("model3.json", payload["formatLabels"]["live2d"])
        self.assertEqual(payload["formatLabels"]["model3d"], "GLB / GLTF / VRM / FBX / OBJ")
        self.assertEqual(payload["formatLabels"]["unknown"], "与素材类型匹配的文件")
        self.assertEqual(payload["formatLabels"]["customFallback"], "自定义兜底")
        self.assertIn("image/*", payload["smartAccept"])
        self.assertIn(".moc3", payload["smartAccept"])
        self.assertEqual(payload["smartAccept"].count("image/*"), 1)


if __name__ == "__main__":
    unittest.main()
