from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "script_import_mapping.js"


class FrontendScriptImportMappingModuleTests(unittest.TestCase):
    def test_script_import_mapping_matches_project_assets_and_characters(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorScriptImportMapping;
            const character = {{
              id: "char_yuina",
              name: "Yuina",
              displayName: "悠奈",
              expressions: [
                {{ id: "expr_default", name: "默认" }},
                {{ id: "expr_smile", name: "Smile", tags: ["微笑"] }},
              ],
            }};
            const data = {{
              characters: [character],
              charactersById: new Map([["char_yuina", character]]),
              assetList: [
                {{ id: "bg_classroom", type: "background", name: "Classroom", fileName: "classroom.png", tags: ["教室"] }},
                {{ id: "bgm_school", type: "bgm", name: "School Theme", fileName: "school_theme.ogg" }},
                {{ id: "sfx_door", type: "sfx", name: "Door Knock", fileName: "door_knock.wav" }},
                {{ id: "voice_yuina_001", type: "voice", name: "Yuina 001", fileName: "yuina_001.ogg" }},
                {{ id: "cg_school", type: "cg", name: "school_theme_cg.png" }},
              ],
              scenes: [
                {{ id: "scene_roof", name: "Rooftop", tags: ["天台"] }},
                {{ id: "scene_end", name: "Ending" }},
              ],
            }};
            const resolvers = {{
              getSpeakerCharacterId: (hint) => tools.findImportedCharacterByHint(data, hint)?.id ?? "char_fallback",
              findCharacterIdByHint: (hint) => tools.findImportedCharacterByHint(data, hint)?.id ?? "char_fallback",
              findExpressionIdByHint: (characterId, hint) => tools.findImportedExpressionIdByHint(data, characterId, hint),
              findAssetIdByHint: (hint, types) => tools.findImportedAssetIdByHint(data, hint, types),
              findSceneIdByHint: (hint) => tools.findImportedSceneIdByHint(data, hint),
              getDefaultCharacterPosition: () => "center",
              getSafePosition: (value) => ["left", "center", "right"].includes(value) ? value : "center",
              getSafeTransition: (value) => ["fade", "dissolve", "none"].includes(value) ? value : "fade",
              getSafeTransitionDurationMs: (value, fallback = 600) => Number.parseInt(value, 10) || fallback,
              getSafeNonNegativeNumber: (value, fallback = 0) => Math.max(0, Number.parseFloat(value) || fallback),
              getSafeVolumePercent: (value, fallback = 100) => Math.max(0, Math.min(100, Number.parseInt(value, 10) || fallback)),
              getSafeFadeAction: (value) => value === "fade_in" ? "fade_in" : "fade_out",
              getEffectDuration: (value) => tools.getImportedEffectDuration(value),
              getDefaultJumpTargetSceneId: () => "scene_end",
              defaultCharacterStage: {{ scale: 1, opacity: 1 }},
              choiceContinueTarget: "__continue__",
            }};
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              normalized: tools.normalizeImportedLookupText("School Theme.ogg"),
              characterByRomaji: tools.findImportedCharacterByHint(data, "yuina")?.id,
              characterByDisplayName: tools.findImportedCharacterByHint(data, "悠奈")?.id,
              expressionByTag: tools.findImportedExpressionIdByHint(data, "char_yuina", "微笑"),
              backgroundByFile: tools.findImportedAssetIdByHint(data, "classroom", ["background"]),
              bgmByName: tools.findImportedAssetIdByHint(data, "school_theme", ["bgm"]),
              sfxByFile: tools.findImportedAssetIdByHint(data, "door_knock", ["sfx"]),
              voiceByFile: tools.findImportedAssetIdByHint(data, "yuina_001", ["voice"]),
              typedLookupDoesNotCrossAssetTypes: tools.findImportedAssetIdByHint(data, "school_theme", ["background"]),
              sceneByName: tools.findImportedSceneIdByHint(data, "rooftop"),
              sceneByTag: tools.findImportedSceneIdByHint(data, "天台"),
              shortDuration: tools.getImportedEffectDuration(300),
              mediumDuration: tools.getImportedEffectDuration(700),
              longDuration: tools.getImportedEffectDuration(1200),
              normalizedDialogue: tools.normalizeImportedDraftBlockForScene(
                {{ type: "dialogue", speakerName: "Yuina", text: " hi ", voiceHint: "yuina_001" }},
                null,
                resolvers
              ),
              normalizedChoice: tools.normalizeImportedDraftBlockForScene(
                {{ type: "choice", options: [{{ text: " roof ", targetHint: "rooftop" }}, {{ text: "stay" }}] }},
                null,
                resolvers
              ),
              normalizedCharacterShow: tools.normalizeImportedDraftBlockForScene(
                {{ type: "character_show", characterHint: "Yuina", expressionHint: "微笑", position: "right", transition: "dissolve", transitionDurationMs: "720" }},
                null,
                resolvers
              ),
              normalizedSfx: tools.normalizeImportedDraftBlockForScene(
                {{ type: "sfx_play", assetHint: "door_knock", volume: "80" }},
                null,
                resolvers
              ),
              normalizedJumpFallback: tools.normalizeImportedDraftBlockForScene(
                {{ type: "jump", targetHint: "unknown" }},
                {{ id: "scene_start" }},
                resolvers
              ),
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
        self.assertIn("findImportedAssetIdByHint", payload["keys"])
        self.assertEqual(payload["normalized"], "schooltheme")
        self.assertEqual(payload["characterByRomaji"], "char_yuina")
        self.assertEqual(payload["characterByDisplayName"], "char_yuina")
        self.assertEqual(payload["expressionByTag"], "expr_smile")
        self.assertEqual(payload["backgroundByFile"], "bg_classroom")
        self.assertEqual(payload["bgmByName"], "bgm_school")
        self.assertEqual(payload["sfxByFile"], "sfx_door")
        self.assertEqual(payload["voiceByFile"], "voice_yuina_001")
        self.assertEqual(payload["typedLookupDoesNotCrossAssetTypes"], "")
        self.assertEqual(payload["sceneByName"], "scene_roof")
        self.assertEqual(payload["sceneByTag"], "scene_roof")
        self.assertEqual(payload["shortDuration"], "short")
        self.assertEqual(payload["mediumDuration"], "medium")
        self.assertEqual(payload["longDuration"], "long")
        self.assertIn("normalizeImportedDraftBlockForScene", payload["keys"])
        self.assertEqual(
            payload["normalizedDialogue"],
            {
                "type": "dialogue",
                "speakerId": "char_yuina",
                "text": "hi",
                "voiceAssetId": "voice_yuina_001",
                "voiceVolume": 100,
            },
        )
        self.assertEqual(
            payload["normalizedChoice"],
            {
                "type": "choice",
                "options": [
                    {"text": "roof", "gotoSceneId": "scene_roof"},
                    {"text": "stay", "gotoSceneId": "__continue__"},
                ],
            },
        )
        self.assertEqual(payload["normalizedCharacterShow"]["characterId"], "char_yuina")
        self.assertEqual(payload["normalizedCharacterShow"]["expressionId"], "expr_smile")
        self.assertEqual(payload["normalizedCharacterShow"]["position"], "right")
        self.assertEqual(payload["normalizedCharacterShow"]["transition"], "dissolve")
        self.assertEqual(payload["normalizedCharacterShow"]["transitionDurationMs"], 720)
        self.assertEqual(payload["normalizedCharacterShow"]["stage"], {"scale": 1, "opacity": 1})
        self.assertEqual(payload["normalizedSfx"], {"type": "sfx_play", "assetId": "sfx_door", "volume": 80})
        self.assertEqual(payload["normalizedJumpFallback"], {"type": "jump", "targetSceneId": "scene_end"})


if __name__ == "__main__":
    unittest.main()
