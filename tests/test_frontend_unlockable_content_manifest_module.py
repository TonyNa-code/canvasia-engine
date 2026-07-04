from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "unlockable_content_manifest.js"


class FrontendUnlockableContentManifestModuleTests(unittest.TestCase):
    def test_unlockable_content_manifest_collects_gallery_replay_archive_and_ending_gaps(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorUnlockableContentManifest;
            const data = {{
              project: {{ title: "Unlock Demo" }},
              assetList: [
                {{ id: "cg_ready", type: "cg", name: "告白 CG", path: "assets/cg_ready.png", fileExists: true }},
                {{ id: "cg_missing", type: "cg", name: "回忆 CG", fileExists: false }},
                {{ id: "bgm_ready", type: "bgm", name: "放课后钢琴", path: "assets/bgm_ready.ogg", fileExists: true }},
                {{ id: "bgm_missing", type: "bgm", name: "雨夜主题", fileExists: false }},
                {{ id: "voice_ready", type: "voice", name: "女主 001", path: "assets/voice_ready.ogg", fileExists: true }},
                {{ id: "voice_missing", type: "voice", name: "好友 001", fileExists: false }},
                {{ id: "bg_ready", type: "background", name: "教室", path: "assets/bg_ready.png", fileExists: true }},
                {{ id: "bg_missing", type: "background", name: "天台", fileExists: false }},
                {{ id: "sprite_ready", type: "sprite", name: "女主立绘", path: "assets/hero.png", fileExists: true }},
                {{ id: "sprite_missing", type: "sprite", name: "好友立绘", fileExists: false }},
              ],
              assetUsage: {{
                cg_ready: [{{ label: "回想馆" }}],
                bgm_ready: [{{ label: "开场 BGM" }}],
                bgm_missing: [{{ label: "雨夜 BGM" }}],
              }},
              characters: [
                {{ id: "hero", name: "女主", defaultSpriteId: "sprite_ready" }},
                {{ id: "side", name: "好友", defaultSpriteId: "sprite_missing" }},
              ],
              chapters: [
                {{
                  id: "chapter_1",
                  name: "开学第一天",
                  scenes: [
                    {{
                      id: "scene_start",
                      name: "教室黄昏",
                      blocks: [
                        {{ id: "bg_1", type: "background", assetId: "bg_ready" }},
                        {{ id: "music_1", type: "music_play", assetId: "bgm_ready" }},
                        {{ id: "narr_1", type: "narration", text: "窗外的云像被谁轻轻推开。" }},
                        {{ id: "line_1", type: "dialogue", characterId: "hero", text: "欢迎回来。", voiceAssetId: "voice_ready" }},
                        {{ id: "line_2", type: "dialogue", characterId: "side", text: "你也太慢了吧。", voiceAssetId: "voice_missing" }},
                        {{ id: "choice_1", type: "choice", choices: [{{ text: "去天台", targetSceneId: "scene_roof" }}] }},
                      ],
                    }},
                    {{
                      id: "scene_roof",
                      name: "天台晚风",
                      blocks: [
                        {{ id: "bg_2", type: "background", assetId: "bg_missing" }},
                        {{ id: "music_2", type: "music_play", assetId: "bgm_missing" }},
                        {{ id: "line_3", type: "dialogue", characterId: "hero", text: "这里的风还是一样。" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const routeOverview = {{
              metrics: {{ sceneCount: 2 }},
              endingPaths: [
                {{ id: "ending_good", name: "Good Ending", sceneId: "scene_roof", reachable: true, pathLabel: "教室黄昏 -> 天台晚风" }},
                {{ id: "ending_hidden", name: "Hidden Ending", sceneId: "scene_hidden", reachable: false }},
              ],
            }};
            const manifest = tools.buildUnlockableContentManifest(data, {{ routeOverview }});
            const digest = tools.getUnlockableContentStatusDigest(manifest);
            const markdown = tools.buildUnlockableContentMarkdown(manifest, {{ generatedAt: "2026-07-05 00:00:00" }});
            const csv = tools.buildUnlockableContentCsv(manifest);
            const panel = tools.renderUnlockableContentManifestPanel(manifest);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              manifest,
              digest,
              markdown,
              csv,
              panel,
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
        self.assertIn("buildUnlockableContentManifest", payload["keys"])
        self.assertIn("buildUnlockableContentMarkdown", payload["keys"])
        self.assertIn("buildUnlockableContentCsv", payload["keys"])
        self.assertIn("renderUnlockableContentManifestPanel", payload["keys"])

        manifest = payload["manifest"]
        self.assertEqual(manifest["projectTitle"], "Unlock Demo")
        self.assertEqual(manifest["summary"]["groupCount"], 10)
        self.assertGreater(manifest["summary"]["totalEntryCount"], 10)
        self.assertGreater(manifest["summary"]["missingEntryCount"], 0)
        self.assertGreater(manifest["summary"]["achievementCount"], 0)
        self.assertEqual(manifest["summary"]["endingCount"], 2)
        self.assertEqual(manifest["summary"]["reachableEndingCount"], 1)

        group_ids = {group["id"] for group in manifest["groups"]}
        self.assertEqual(
            group_ids,
            {
                "extra_cg",
                "music_room",
                "voice_replay",
                "character_archive",
                "location_archive",
                "narration_archive",
                "relationship_archive",
                "chapter_replay",
                "ending_collection",
                "achievements",
            },
        )
        issue_codes = {issue["code"] for issue in manifest["issues"]}
        self.assertIn("unlockable_asset_missing", issue_codes)
        self.assertIn("unlockable_voice_missing", issue_codes)
        self.assertIn("unlockable_character_visual_missing", issue_codes)
        self.assertIn("unlockable_location_asset_missing", issue_codes)
        self.assertIn("unlockable_ending_unreachable", issue_codes)
        self.assertEqual(payload["digest"]["status"], "warn")
        self.assertIn("# Unlock Demo 可解锁内容清单", payload["markdown"])
        self.assertIn("CG 图鉴", payload["markdown"])
        self.assertIn('"回忆 CG"', payload["csv"])
        self.assertIn('data-action="export-unlockable-content-manifest-markdown"', payload["panel"])
        self.assertIn('data-action="export-unlockable-content-manifest-csv"', payload["panel"])


if __name__ == "__main__":
    unittest.main()
