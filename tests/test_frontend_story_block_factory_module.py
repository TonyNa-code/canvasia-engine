from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FACTORY_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_factory.js"
ACTIONS_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_actions.js"


class FrontendStoryBlockFactoryModuleTests(unittest.TestCase):
    def test_factory_covers_every_registered_add_action_without_shared_mutable_defaults(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(ACTIONS_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(FACTORY_PATH))}, "utf8"), context);
            const actionTools = context.window.CanvasiaEditorStoryBlockActions;
            const factory = context.window.CanvasiaEditorStoryBlockFactory;
            const scene = {{
              id: "scene_start",
              blocks: [
                {{ type: "stage_image" }},
                {{ type: "achievement_unlock" }},
              ],
            }};
            const options = {{
              blockId: "block_test",
              selectedSceneId: "scene_start",
              selectedCharacterId: "hero",
              characters: [{{ id: "hero" }}],
              variables: [{{ id: "route", defaultValue: "common" }}],
              assetList: [
                {{ id: "bg_room", type: "background" }},
                {{ id: "bgm_theme", type: "bgm" }},
                {{ id: "sfx_click", type: "sfx" }},
                {{ id: "video_op", type: "video" }},
              ],
              defaultStageImageTransform: {{ width: 62, opacity: 90 }},
              defaultCharacterStage: {{ scale: 110, opacity: 100 }},
              getSafeExpressionId() {{ return "default"; }},
              createDefaultChoiceOptions(blockId, sceneId) {{ return [{{ id: `${{blockId}}_1`, gotoSceneId: sceneId }}]; }},
              getSafeStageImageAssetId() {{ return "prop_note"; }},
              getDefaultCharacterPosition() {{ return "right"; }},
              getSafeAssetIdByType(type) {{ return {{ bgm: "bgm_theme", sfx: "sfx_click", video: "video_op" }}[type] ?? ""; }},
              sanitizeMusicTransport() {{ return {{ loop: true, restartMode: "continue" }}; }},
              sanitizeSfxTransport() {{ return {{ channelId: "effect", loop: false, restartMode: "restart", volume: 100 }}; }},
              sanitizeSfxStop() {{ return {{ channelId: "all", fadeOutMs: 600 }}; }},
              sanitizeVideoTransport() {{ return {{ autoplay: true, loop: false, fit: "contain" }}; }},
              buildDefaultParticleEffectConfig() {{ return {{ action: "start", preset: "snow" }}; }},
              getSafeScreenColorGrade() {{ return {{ brightness: 5 }}; }},
              getDefaultJumpTargetSceneId() {{ return "scene_next"; }},
              getSafeVariableId(value, expectedType) {{ return value || (Array.isArray(expectedType) ? "player_name" : "affection"); }},
              getVariableDefaultValue() {{ return "common"; }},
              createDefaultConditionBranches(blockId) {{ return [{{ id: `${{blockId}}_if`, gotoSceneId: "scene_next" }}]; }},
            }};
            const entries = actionTools.getAddBlockActionEntries();
            const blocks = entries.map((entry) => factory.createDefaultStoryBlock(scene, entry.blockType, options));
            const byType = Object.fromEntries(blocks.map((block) => [block.type, block]));
            const firstCharacter = factory.createDefaultStoryBlock(scene, "character_show", options);
            const secondCharacter = factory.createDefaultStoryBlock(scene, "character_show", options);
            firstCharacter.stage.scale = 999;
            const unknown = factory.createDefaultStoryBlock(scene, "custom_future_card", options);
            process.stdout.write(JSON.stringify({{
              actionTypes: entries.map((entry) => entry.blockType),
              createdTypes: blocks.map((block) => block.type),
              byType,
              secondCharacterScale: secondCharacter.stage.scale,
              unknown,
              globalAttached: Boolean(factory),
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
        self.assertEqual(payload["createdTypes"], payload["actionTypes"])
        self.assertEqual(payload["byType"]["dialogue"]["speakerId"], "hero")
        self.assertEqual(payload["byType"]["dialogue"]["expressionId"], "default")
        self.assertEqual(payload["byType"]["background"]["assetId"], "bg_room")
        self.assertEqual(payload["byType"]["stage_image"]["layerId"], "layer_2")
        self.assertEqual(payload["byType"]["achievement_unlock"]["achievementId"], "story_achievement_2")
        self.assertEqual(payload["byType"]["sfx_play"]["assetId"], "sfx_click")
        self.assertEqual(payload["byType"]["sfx_stop"]["channelId"], "all")
        self.assertEqual(payload["byType"]["condition"]["elseGotoSceneId"], "scene_next")
        self.assertEqual(payload["secondCharacterScale"], 110)
        self.assertEqual(payload["unknown"], {"id": "block_test", "type": "custom_future_card"})
        self.assertTrue(payload["globalAttached"])


if __name__ == "__main__":
    unittest.main()
