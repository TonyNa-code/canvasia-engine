from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
STORY_BLOCK_CATALOG_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_catalog.js"
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "asset_usage_map.js"


class FrontendAssetUsageMapModuleTests(unittest.TestCase):
    def test_asset_usage_map_tracks_story_character_and_project_ui_references(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(STORY_BLOCK_CATALOG_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorAssetUsageMap;
            const data = {{
              project: {{
                dialogBoxConfig: {{ panelAssetId: "ui_panel" }},
                gameUiConfig: {{
                  fontAssetId: "font_main",
                  titleLogoAssetId: "logo_main",
                  buttonHoverFrameAssetId: "ui_button_hover",
                }},
              }},
              characters: [
                {{
                  id: "char_a",
                  displayName: "林若曦",
                  defaultSpriteId: "sprite_default",
                  presentation: {{
                    mode: "live2d",
                    fallbackSpriteAssetId: "sprite_fallback",
                    live2d: {{ modelAssetId: "live2d_model" }},
                    model3d: {{ modelAssetId: "model3d_entry" }},
                  }},
                  expressions: [
                    {{
                      id: "smile",
                      name: "微笑",
                      spriteAssetId: "sprite_smile",
                      layerAssetIds: ["sprite_layer_blush", "sprite_layer_tears"],
                    }},
                  ],
                }},
              ],
              chapters: [
                {{
                  chapterId: "chapter_1",
                  name: "第1章",
                  scenes: [
                    {{
                      id: "scene_start",
                      name: "教室黄昏",
                      blocks: [
                        {{ id: "bg", type: "background", assetId: "bg_classroom" }},
                        {{ id: "music", type: "music_play", assetId: "bgm_theme" }},
                        {{ id: "line", type: "dialogue", speakerId: "char_a", expressionId: "smile", text: "你好", voiceAssetId: "voice_001" }},
                        {{ id: "particle", type: "particle_effect", assetId: "ui_snowflake" }},
                        {{ id: "prop", type: "stage_image", action: "show", layerId: "letter", assetId: "prop_letter" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            data.charactersById = new Map(data.characters.map((character) => [character.id, character]));
            const usage = tools.buildAssetUsageMap(data);
            const payload = {{
              keys: Object.keys(tools).sort(),
              uiPanel: usage.get("ui_panel"),
              logoMain: usage.get("logo_main"),
              defaultSprite: usage.get("sprite_default"),
              live2d: usage.get("live2d_model"),
              model3d: usage.get("model3d_entry"),
              smileSprite: usage.get("sprite_smile"),
              blushLayer: usage.get("sprite_layer_blush"),
              voice: usage.get("voice_001"),
              bgm: usage.get("bgm_theme"),
              particle: usage.get("ui_snowflake"),
              stageImage: usage.get("prop_letter"),
              countVoice: tools.getAssetUsageCount("voice_001", {{ assetUsage: usage }}),
              missingCount: tools.getAssetUsageCount("missing_asset", {{ assetUsage: usage }}),
            }};
            process.stdout.write(JSON.stringify(payload));
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
        self.assertIn("buildAssetUsageMap", payload["keys"])
        self.assertIn("getAssetUsageCount", payload["keys"])
        self.assertEqual(payload["uiPanel"][0]["kind"], "project")
        self.assertIn("文本框自定义贴图", payload["uiPanel"][0]["label"])
        self.assertIn("标题 Logo", payload["logoMain"][0]["label"])
        self.assertIn("角色默认立绘", payload["defaultSprite"][0]["label"])
        self.assertIn("Live2D", payload["live2d"][0]["label"])
        self.assertIn("3D 模型", payload["model3d"][0]["label"])
        self.assertEqual(payload["smileSprite"][0]["kind"], "character")
        self.assertEqual(payload["smileSprite"][1]["kind"], "story")
        self.assertIn("场景：教室黄昏", payload["smileSprite"][1]["label"])
        self.assertIn("差分", payload["blushLayer"][0]["label"])
        self.assertEqual(payload["voice"][0]["sceneId"], "scene_start")
        self.assertIn("播放音乐", payload["bgm"][0]["label"])
        self.assertIn("粒子特效", payload["particle"][0]["label"])
        self.assertIn("舞台贴图", payload["stageImage"][0]["label"])
        self.assertEqual(payload["countVoice"], 1)
        self.assertEqual(payload["missingCount"], 0)


if __name__ == "__main__":
    unittest.main()
