from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_scene_prefetch.js"


class FrontendRuntimeScenePrefetchModuleTests(unittest.TestCase):
    def test_scene_prefetch_collects_upcoming_and_branch_assets(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const assetsById = new Map([
              ["bg_hall", {{ id: "bg_hall", type: "background", name: "走廊", exportUrl: "assets/background/hall.png", fileSizeBytes: 4096 }}],
              ["bg_roof", {{ id: "bg_roof", type: "background", name: "屋顶", exportUrl: "assets/background/roof.png" }}],
              ["bg_secret", {{ id: "bg_secret", type: "background", name: "秘密房间", exportUrl: "assets/background/secret.png" }}],
              ["bg_missing", {{ id: "bg_missing", type: "background", name: "缺失", exportUrl: "", isMissing: true }}],
              ["sprite_yuina_smile", {{ id: "sprite_yuina_smile", type: "sprite", name: "由依笑", exportUrl: "assets/sprite/yuina-smile.png" }}],
              ["voice_001", {{ id: "voice_001", type: "voice", name: "第一句语音", exportUrl: "assets/voice/001.ogg" }}],
              ["bgm_roof", {{ id: "bgm_roof", type: "bgm", name: "屋顶风", exportUrl: "assets/bgm/roof.ogg" }}],
              ["op_video", {{ id: "op_video", type: "video", name: "OP", exportUrl: "assets/video/op.mp4" }}],
            ]);
            const charactersById = new Map([
              ["yuina", {{
                id: "yuina",
                defaultSpriteId: "sprite_yuina_smile",
                expressions: [{{ id: "smile", spriteAssetId: "sprite_yuina_smile" }}],
              }}],
            ]);
            const scenesById = new Map([
              ["intro", {{
                id: "intro",
                blocks: [
                  {{ id: "b0", type: "narration", text: "start" }},
                  {{ id: "b1", type: "background", assetId: "bg_hall" }},
                  {{ id: "b2", type: "dialogue", speakerId: "yuina", expressionId: "smile", voiceAssetId: "voice_001", text: "走吧" }},
                  {{ id: "b3", type: "choice", options: [
                    {{ id: "go_roof", text: "上楼", gotoSceneId: "roof" }},
                    {{ id: "go_secret", text: "留下", gotoSceneId: "secret" }},
                  ] }},
                ],
              }}],
              ["roof", {{
                id: "roof",
                blocks: [
                  {{ id: "r0", type: "background", assetId: "bg_roof" }},
                  {{ id: "r1", type: "music_play", assetId: "bgm_roof" }},
                  {{ id: "r2", type: "video_play", assetId: "op_video" }},
                ],
              }}],
              ["secret", {{
                id: "secret",
                blocks: [
                  {{ id: "s0", type: "background", assetId: "bg_secret" }},
                  {{ id: "s1", type: "background", assetId: "bg_missing" }},
                ],
              }}],
            ]);

            const manifest = tools.buildRuntimeScenePrefetchManifest(
              {{
                sceneId: "intro",
                blockId: "b0",
                blockIndex: 0,
                choiceOptions: [
                  {{ id: "go_roof", gotoSceneId: "roof" }},
                  {{ id: "go_secret", gotoSceneId: "secret" }},
                ],
              }},
              {{ scenesById, assetsById, charactersById }},
              {{ blockLookahead: 6, targetBlockLookahead: 4, maxEntries: 12 }}
            );
            const summary = tools.getRuntimeScenePrefetchSummary(manifest);

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              generatedBy: manifest.generatedBy,
              targetSceneIds: manifest.targetSceneIds,
              ids: manifest.entries.map((entry) => entry.assetId),
              phases: Object.fromEntries(manifest.entries.map((entry) => [entry.assetId, entry.phase])),
              reasons: Object.fromEntries(manifest.entries.map((entry) => [entry.assetId, entry.reason])),
              summary,
              prefetchKey: manifest.prefetchKey,
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
        self.assertIn("buildRuntimeScenePrefetchManifest", payload["keys"])
        self.assertIn("getRuntimeScenePrefetchSummary", payload["keys"])
        self.assertEqual(payload["generatedBy"], "runtime_scene_prefetch")
        self.assertEqual(payload["targetSceneIds"], ["roof", "secret"])
        self.assertIn("bg_hall", payload["ids"])
        self.assertIn("sprite_yuina_smile", payload["ids"])
        self.assertIn("voice_001", payload["ids"])
        self.assertIn("bg_roof", payload["ids"])
        self.assertIn("bgm_roof", payload["ids"])
        self.assertIn("op_video", payload["ids"])
        self.assertIn("bg_secret", payload["ids"])
        self.assertNotIn("bg_missing", payload["ids"])
        self.assertEqual(payload["phases"]["bg_hall"], "early")
        self.assertEqual(payload["phases"]["bg_roof"], "early")
        self.assertEqual(payload["summary"]["imageCount"], 4)
        self.assertEqual(payload["summary"]["audioCount"], 2)
        self.assertEqual(payload["summary"]["videoCount"], 1)
        self.assertIn("intro:b0:0", payload["prefetchKey"])

    def test_scene_prefetch_excludes_already_scheduled_assets_and_empty_snapshots(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const assetsById = new Map([
              ["bg_next", {{ id: "bg_next", type: "background", exportUrl: "assets/bg-next.png" }}],
              ["voice_next", {{ id: "voice_next", type: "voice", exportUrl: "assets/voice-next.ogg" }}],
            ]);
            const scenesById = new Map([
              ["scene_a", {{
                id: "scene_a",
                blocks: [
                  {{ id: "a0", type: "narration", text: "now" }},
                  {{ id: "a1", type: "background", assetId: "bg_next" }},
                  {{ id: "a2", type: "narration", voiceAssetId: "voice_next", text: "next" }},
                ],
              }}],
            ]);

            const manifest = tools.buildRuntimeScenePrefetchManifest(
              {{ sceneId: "scene_a", blockId: "a0", blockIndex: 0, choiceOptions: [] }},
              {{ scenesById, assetsById, excludeAssetIds: new Set(["bg_next"]) }},
              {{ blockLookahead: 4 }}
            );
            const emptyManifest = tools.buildRuntimeScenePrefetchManifest(
              {{ sceneId: "missing", blockId: "x", blockIndex: 0, choiceOptions: [] }},
              {{ scenesById, assetsById }},
              {{}}
            );

            process.stdout.write(JSON.stringify({{
              ids: manifest.entries.map((entry) => entry.assetId),
              total: manifest.entries.length,
              emptyTotal: emptyManifest.entries.length,
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
        self.assertEqual(payload["ids"], ["voice_next"])
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["emptyTotal"], 0)


if __name__ == "__main__":
    unittest.main()
