from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "asset_dependency_sheet.js"


class FrontendAssetDependencySheetModuleTests(unittest.TestCase):
    def test_asset_dependency_sheet_helpers_export_markdown_and_csv(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorAssetDependencySheet;
            const data = {{
              project: {{
                title: "Demo Project",
                dialogBoxConfig: {{ panelAssetId: "ui_panel" }},
                gameUiConfig: {{
                  fontAssetId: "font_main",
                  titleBackgroundAssetId: "bg_ready",
                  titleLogoAssetId: "missing_logo",
                  buttonFrameAssetId: "bg_ready",
                }},
              }},
              assetList: [
                {{ id: "bg_ready", type: "background", name: "可用背景", path: "assets/bg_ready.png", fileExists: true }},
                {{ id: "bg_missing", type: "background", name: "缺文件背景", path: "assets/bg_missing.png", fileExists: false }},
                {{ id: "sfx_click", type: "sfx", name: "点击音", path: "assets/click.wav", fileExists: true }},
                {{ id: "sprite_happy", type: "sprite", name: "微笑立绘", path: "assets/sprite.png", fileExists: true }},
                {{ id: "bgm_theme", type: "bgm", name: "主题曲", path: "assets/theme.ogg", fileExists: true }},
                {{ id: "voice_001", type: "voice", name: "第一句语音", path: "assets/voice.wav", fileExists: true }},
                {{ id: "ui_panel", type: "ui", name: "对话框图层", path: "assets/ui_panel.png", fileExists: false }},
                {{ id: "font_main", type: "font", name: "正文字体", path: "assets/font.ttf", fileExists: true }},
                {{ id: "unused_cg", type: "cg", name: "暂未使用 CG", path: "assets/unused.png", fileExists: true }},
              ],
              characters: [
                {{
                  id: "char_a",
                  displayName: "林若曦",
                  defaultSpriteId: "sprite_happy",
                  expressions: [
                    {{ id: "smile", name: "微笑", spriteAssetId: "sprite_happy", layerAssetIds: ["ui_panel"] }},
                  ],
                  presentation: {{
                    mode: "sprite",
                    fallbackSpriteAssetId: "",
                    live2d: {{ modelAssetId: "" }},
                    model3d: {{ modelAssetId: "" }},
                  }},
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
                        {{ id: "bg_missing_block", type: "background", assetId: "bg_missing" }},
                        {{ id: "bg_wrong_type", type: "background", assetId: "sfx_click" }},
                        {{ id: "music", type: "music_play", assetId: "bgm_theme" }},
                        {{ id: "sfx", type: "sfx_play", assetId: "sfx_click" }},
                        {{ id: "line", type: "dialogue", speakerId: "char_a", expressionId: "smile", text: "你好", voiceAssetId: "voice_001" }},
                        {{ id: "particle", type: "particle_effect", assetId: "asset_ghost" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const sheet = tools.buildAssetDependencySheet(data);
            const digest = tools.getAssetDependencyStatusDigest(sheet);
            const markdown = tools.buildAssetDependencyMarkdown(sheet, {{
              projectTitle: "Demo Project",
              generatedAt: "2026-07-04 01:00:00",
            }});
            const csv = tools.buildAssetDependencyCsv(sheet);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              sheet,
              digest,
              markdown,
              csv,
              backgroundLabel: tools.getAssetTypeLabel("background"),
              uiScopeLabel: tools.getReferenceScopeLabel("ui"),
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
        self.assertIn("buildAssetDependencySheet", payload["keys"])
        self.assertIn("buildAssetDependencyMarkdown", payload["keys"])
        self.assertIn("buildAssetDependencyCsv", payload["keys"])
        self.assertEqual(payload["sheet"]["summary"]["assetCount"], 9)
        self.assertEqual(payload["sheet"]["summary"]["unknownReferenceCount"], 2)
        self.assertEqual(payload["sheet"]["summary"]["urgentMissingCount"], 2)
        self.assertGreaterEqual(payload["sheet"]["summary"]["typeMismatchCount"], 2)
        self.assertGreater(payload["sheet"]["summary"]["storyReferenceCount"], 0)
        self.assertGreater(payload["sheet"]["summary"]["characterReferenceCount"], 0)
        self.assertGreater(payload["sheet"]["summary"]["uiReferenceCount"], 0)
        self.assertGreater(payload["sheet"]["summary"]["unusedAssetCount"], 0)
        self.assertEqual(payload["digest"]["status"], "blocked")
        issue_codes = [issue["code"] for issue in payload["sheet"]["issues"]]
        self.assertIn("asset_file_missing", issue_codes)
        self.assertIn("asset_reference_type_mismatch", issue_codes)
        self.assertIn("asset_reference_unknown", issue_codes)
        self.assertIn("asset_unused", issue_codes)
        self.assertIn("# Demo Project 素材依赖表", payload["markdown"])
        self.assertIn("缺文件背景", payload["markdown"])
        self.assertIn('"对话框图层"', payload["csv"])
        self.assertEqual(payload["backgroundLabel"], "背景")
        self.assertEqual(payload["uiScopeLabel"], "项目 UI")


if __name__ == "__main__":
    unittest.main()
