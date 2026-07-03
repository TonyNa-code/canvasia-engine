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
                {{ id: "video_opening", type: "video", name: "Opening Movie", fileName: "opening_movie.mp4" }},
                {{ id: "cg_school", type: "cg", name: "school_theme_cg.png" }},
              ],
              variables: [
                {{ id: "affection", type: "number", name: "Affection", displayName: "好感度", tags: ["好感"] }},
                {{ id: "met", type: "boolean", name: "Met Heroine", displayName: "是否见过" }},
                {{ id: "route", type: "string", name: "Route", displayName: "路线" }},
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
              findVariableIdByHint: (hint, typeFilter = "") => tools.findImportedVariableIdByHint(data, hint, typeFilter),
              getDefaultCharacterPosition: () => "center",
              getSafePosition: (value) => ["left", "center", "right"].includes(value) ? value : "center",
              getSafeTransition: (value) => ["fade", "dissolve", "none"].includes(value) ? value : "fade",
              getSafeTransitionDurationMs: (value, fallback = 600) => Number.parseInt(value, 10) || fallback,
              getSafeNonNegativeNumber: (value, fallback = 0) => Math.max(0, Number.parseFloat(value) || fallback),
              getSafeVolumePercent: (value, fallback = 100) => Math.max(0, Math.min(100, Number.parseInt(value, 10) || fallback)),
              getSafeTextSpeed: (value) => ["slow", "normal", "fast", "instant"].includes(value) ? value : "normal",
              getSafeVideoFit: (value) => ["contain", "cover", "fill"].includes(value) ? value : "contain",
              getSafeVideoVolume: (value) => Math.max(0, Math.min(100, Number.parseInt(value, 10) || 100)),
              getSafeShakeIntensity: (value) => ["light", "medium", "heavy"].includes(value) ? value : "medium",
              getSafeEffectDuration: (value) => ["short", "medium", "long"].includes(value) ? value : "medium",
              getSafeFlashColor: (value) => ["white", "warm", "red", "black"].includes(value) ? value : "white",
              getSafeFlashIntensity: (value) => ["soft", "medium", "strong"].includes(value) ? value : "medium",
              getSafeCameraZoomAction: (value) => ["zoom_in", "zoom_out", "reset"].includes(value) ? value : "zoom_in",
              getSafeCameraZoomStrength: (value) => ["light", "medium", "heavy"].includes(value) ? value : "medium",
              getSafeCameraZoomFocus: (value) => ["left", "center", "right"].includes(value) ? value : "center",
              getSafeCameraPanTarget: (value) => ["left", "center", "right"].includes(value) ? value : "center",
              getSafeCameraPanStrength: (value) => ["light", "medium", "heavy"].includes(value) ? value : "medium",
              getSafeCreditsDuration: (value) => Math.max(4, Math.min(180, Number.parseInt(value, 10) || 18)),
              getSafeCreditsBackground: (value) => ["dark", "light", "transparent"].includes(value) ? value : "dark",
              getSafeWaitDurationSeconds: (value) => Math.round(Math.max(0.1, Math.min(30, Number.parseFloat(value) || 1)) * 10) / 10,
              getSafeFadeAction: (value) => value === "fade_in" ? "fade_in" : "fade_out",
              getSafeScreenFilterAction: (value) => ["apply", "clear"].includes(value) ? value : "apply",
              getSafeScreenFilterPreset: (value) => ["memory", "mono", "dream", "cold"].includes(value) ? value : "memory",
              getSafeScreenFilterStrength: (value) => ["soft", "medium", "strong"].includes(value) ? value : "medium",
              getSafeScreenColorGrade: (value) => value && typeof value === "object" ? {{ ...value, safe: true }} : {{ safe: true }},
              getSafeDepthBlurAction: (value) => ["apply", "clear"].includes(value) ? value : "apply",
              getSafeDepthBlurFocus: (value) => ["left", "center", "right", "full"].includes(value) ? value : "center",
              getSafeDepthBlurStrength: (value) => ["soft", "medium", "strong"].includes(value) ? value : "medium",
              getSafeParticleAction: (value) => ["start", "stop"].includes(value) ? value : "start",
              getSafeParticlePreset: (value) => ["snow", "rain", "petals", "dust", "embers", "sparkles", "bubbles", "confetti", "smoke", "flame", "stardust", "glyphs"].includes(value) ? value : "snow",
              getSafeParticleIntensity: (value) => ["light", "medium", "heavy"].includes(value) ? value : "medium",
              getSafeParticleSpeed: (value) => ["slow", "medium", "fast"].includes(value) ? value : "medium",
              buildDefaultParticleEffectConfig: (preset) => ({{ type: "particle_effect", action: "start", preset, intensity: "medium", speed: "medium", density: 40 }}),
              normalizeParticleEffectConfig: (config) => ({{ ...config, normalized: true }}),
              normalizeChoiceEffect: (effect) => ({{ ...effect, normalized: true }}),
              getSafeConditionOperator: (variableId, value) => {{
                const allowed = variableId === "affection" ? [">=", ">", "<=", "<", "==", "!="] : ["==", "!="];
                return allowed.includes(value) ? value : allowed[0];
              }},
              normalizeVariableValue: (variableId, value) => {{
                if (variableId === "affection") return Number(value) || 0;
                if (variableId === "met") return value === true || value === "true";
                return String(value ?? "");
              }},
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
              videoByFile: tools.findImportedAssetIdByHint(data, "opening_movie", ["video"]),
              typedLookupDoesNotCrossAssetTypes: tools.findImportedAssetIdByHint(data, "school_theme", ["background"]),
              variableById: tools.findImportedVariableIdByHint(data, "affection", "number"),
              variableByDisplayName: tools.findImportedVariableIdByHint(data, "好感度", "number"),
              variableTypeFilterPreventsWrongType: tools.findImportedVariableIdByHint(data, "route", "number"),
              sceneByName: tools.findImportedSceneIdByHint(data, "rooftop"),
              sceneByTag: tools.findImportedSceneIdByHint(data, "天台"),
              shortDuration: tools.getImportedEffectDuration(300),
              mediumDuration: tools.getImportedEffectDuration(700),
              longDuration: tools.getImportedEffectDuration(1200),
              normalizedDialogue: tools.normalizeImportedDraftBlockForScene(
                {{ type: "dialogue", speakerName: "Yuina", text: " hi ", voiceHint: "yuina_001", textSpeed: "fast" }},
                null,
                resolvers
              ),
              normalizedNarration: tools.normalizeImportedDraftBlockForScene(
                {{ type: "narration", text: " wait ", textSpeed: "instant" }},
                null,
                resolvers
              ),
              normalizedChoice: tools.normalizeImportedDraftBlockForScene(
                {{ type: "choice", options: [{{ text: " roof ", targetHint: "rooftop" }}, {{ text: "stay" }}] }},
                null,
                resolvers
              ),
              normalizedChoiceEffects: tools.normalizeImportedDraftBlockForScene(
                {{ type: "choice", options: [
                  {{ text: "拉住她", targetHint: "rooftop", effects: [
                    {{ type: "variable_add", variableHint: "affection", value: 1 }},
                    {{ type: "variable_set", variableHint: "met", value: true }},
                    {{ type: "variable_set", variableHint: "route", value: "good" }},
                    {{ type: "variable_add", variableHint: "route", value: 1 }}
                  ] }}
                ] }},
                null,
                resolvers
              ),
              normalizedVariableSet: tools.normalizeImportedDraftBlockForScene(
                {{ type: "variable_set", variableHint: "route", value: "common" }},
                null,
                resolvers
              ),
              normalizedVariableAdd: tools.normalizeImportedDraftBlockForScene(
                {{ type: "variable_add", variableHint: "affection", value: "2" }},
                null,
                resolvers
              ),
              normalizedVariableAddRejectsNonNumber: tools.normalizeImportedDraftBlockForScene(
                {{ type: "variable_add", variableHint: "route", value: "1" }},
                null,
                resolvers
              ),
              normalizedCharacterShow: tools.normalizeImportedDraftBlockForScene(
                {{ type: "character_show", characterHint: "Yuina", expressionHint: "微笑", position: "right", transition: "dissolve", transitionDurationMs: "720" }},
                null,
                resolvers
              ),
              normalizedCharacterShowWithStage: tools.normalizeImportedDraftBlockForScene(
                {{ type: "character_show", characterHint: "Yuina", expressionHint: "微笑", position: "right", stage: {{ offsetX: -8, offsetY: 3, scale: 118, opacity: 90, layer: 2, flipX: true }} }},
                null,
                resolvers
              ),
              normalizedSfx: tools.normalizeImportedDraftBlockForScene(
                {{ type: "sfx_play", assetHint: "door_knock", volume: "80" }},
                null,
                resolvers
              ),
              normalizedVideo: tools.normalizeImportedDraftBlockForScene(
                {{ type: "video_play", assetHint: "opening_movie", title: "Opening Movie", fit: "cover", volume: "75", startTimeSeconds: "2", endTimeSeconds: "12", skippable: false }},
                null,
                resolvers
              ),
              normalizedCredits: tools.normalizeImportedDraftBlockForScene(
                {{ type: "credits_roll", title: "STAFF", subtitle: "Thanks", lines: ["企划：Tony"], durationSeconds: "24", background: "light", skippable: false }},
                null,
                resolvers
              ),
              normalizedWait: tools.normalizeImportedDraftBlockForScene(
                {{ type: "wait", durationSeconds: "1.2" }},
                null,
                resolvers
              ),
              normalizedShake: tools.normalizeImportedDraftBlockForScene(
                {{ type: "screen_shake", intensity: "heavy", duration: "short" }},
                null,
                resolvers
              ),
              normalizedFlash: tools.normalizeImportedDraftBlockForScene(
                {{ type: "screen_flash", color: "red", intensity: "strong", duration: "long" }},
                null,
                resolvers
              ),
              normalizedZoom: tools.normalizeImportedDraftBlockForScene(
                {{ type: "camera_zoom", action: "zoom_out", strength: "heavy", focus: "right" }},
                null,
                resolvers
              ),
              normalizedPan: tools.normalizeImportedDraftBlockForScene(
                {{ type: "camera_pan", target: "left", strength: "light" }},
                null,
                resolvers
              ),
              normalizedFilter: tools.normalizeImportedDraftBlockForScene(
                {{ type: "screen_filter", action: "apply", preset: "memory", strength: "soft" }},
                null,
                resolvers
              ),
              normalizedFilterClear: tools.normalizeImportedDraftBlockForScene(
                {{ type: "screen_filter", action: "clear", preset: "mono", strength: "strong" }},
                null,
                resolvers
              ),
              normalizedBlur: tools.normalizeImportedDraftBlockForScene(
                {{ type: "depth_blur", action: "apply", focus: "right", strength: "strong" }},
                null,
                resolvers
              ),
              normalizedParticle: tools.normalizeImportedDraftBlockForScene(
                {{ type: "particle_effect", action: "start", preset: "snow", intensity: "heavy", speed: "fast" }},
                null,
                resolvers
              ),
              normalizedParticleStop: tools.normalizeImportedDraftBlockForScene(
                {{ type: "particle_effect", action: "stop", preset: "rain", intensity: "light", speed: "slow" }},
                null,
                resolvers
              ),
              normalizedJumpFallback: tools.normalizeImportedDraftBlockForScene(
                {{ type: "jump", targetHint: "unknown" }},
                {{ id: "scene_start" }},
                resolvers
              ),
              normalizedCondition: tools.normalizeImportedDraftBlockForScene(
                {{ type: "condition", branches: [
                  {{ when: [
                    {{ variableHint: "affection", operator: ">=", value: "2" }},
                    {{ variableHint: "met", operator: "==", value: true }}
                  ], targetHint: "rooftop" }}
                ], elseTargetHint: "ending" }},
                {{ id: "scene_start" }},
                resolvers
              ),
              normalizedConditionDropsUnknownVariable: tools.normalizeImportedDraftBlockForScene(
                {{ type: "condition", branches: [
                  {{ when: [{{ variableHint: "ghost", operator: "==", value: 1 }}], targetHint: "rooftop" }}
                ] }},
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
        self.assertEqual(payload["videoByFile"], "video_opening")
        self.assertEqual(payload["typedLookupDoesNotCrossAssetTypes"], "")
        self.assertEqual(payload["variableById"], "affection")
        self.assertEqual(payload["variableByDisplayName"], "affection")
        self.assertEqual(payload["variableTypeFilterPreventsWrongType"], "")
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
                "textSpeed": "fast",
                "voiceAssetId": "voice_yuina_001",
                "voiceVolume": 100,
            },
        )
        self.assertEqual(payload["normalizedNarration"], {
            "type": "narration",
            "text": "wait",
            "textSpeed": "instant",
        })
        self.assertEqual(
            payload["normalizedChoice"],
            {
                "type": "choice",
                "options": [
                    {"text": "roof", "gotoSceneId": "scene_roof", "effects": []},
                    {"text": "stay", "gotoSceneId": "__continue__", "effects": []},
                ],
            },
        )
        self.assertEqual(payload["normalizedChoiceEffects"], {
            "type": "choice",
            "options": [
                {
                    "text": "拉住她",
                    "gotoSceneId": "scene_roof",
                    "effects": [
                        {"type": "variable_add", "variableId": "affection", "value": 1, "normalized": True},
                        {"type": "variable_set", "variableId": "met", "value": True, "normalized": True},
                        {"type": "variable_set", "variableId": "route", "value": "good", "normalized": True},
                    ],
                },
            ],
        })
        self.assertEqual(payload["normalizedVariableSet"], {
            "type": "variable_set",
            "variableId": "route",
            "value": "common",
        })
        self.assertEqual(payload["normalizedVariableAdd"], {
            "type": "variable_add",
            "variableId": "affection",
            "value": 2,
        })
        self.assertIsNone(payload["normalizedVariableAddRejectsNonNumber"])
        self.assertEqual(payload["normalizedCharacterShow"]["characterId"], "char_yuina")
        self.assertEqual(payload["normalizedCharacterShow"]["expressionId"], "expr_smile")
        self.assertEqual(payload["normalizedCharacterShow"]["position"], "right")
        self.assertEqual(payload["normalizedCharacterShow"]["transition"], "dissolve")
        self.assertEqual(payload["normalizedCharacterShow"]["transitionDurationMs"], 720)
        self.assertEqual(payload["normalizedCharacterShow"]["stage"], {"scale": 1, "opacity": 1})
        self.assertEqual(payload["normalizedCharacterShowWithStage"]["stage"], {
            "scale": 118,
            "opacity": 90,
            "offsetX": -8,
            "offsetY": 3,
            "layer": 2,
            "flipX": True,
        })
        self.assertEqual(payload["normalizedSfx"], {"type": "sfx_play", "assetId": "sfx_door", "volume": 80})
        self.assertEqual(
            payload["normalizedVideo"],
            {
                "type": "video_play",
                "assetId": "video_opening",
                "title": "Opening Movie",
                "fit": "cover",
                "volume": 75,
                "startTimeSeconds": 2,
                "endTimeSeconds": 12,
                "skippable": False,
            },
        )
        self.assertEqual(payload["normalizedCredits"], {
            "type": "credits_roll",
            "title": "STAFF",
            "subtitle": "Thanks",
            "lines": ["企划：Tony"],
            "durationSeconds": 24,
            "background": "light",
            "skippable": False,
        })
        self.assertEqual(payload["normalizedWait"], {"type": "wait", "durationSeconds": 1.2})
        self.assertEqual(payload["normalizedShake"], {"type": "screen_shake", "intensity": "heavy", "duration": "short"})
        self.assertEqual(payload["normalizedFlash"], {
            "type": "screen_flash",
            "color": "red",
            "intensity": "strong",
            "duration": "long",
        })
        self.assertEqual(payload["normalizedZoom"], {
            "type": "camera_zoom",
            "action": "zoom_out",
            "strength": "heavy",
            "focus": "right",
        })
        self.assertEqual(payload["normalizedPan"], {"type": "camera_pan", "target": "left", "strength": "light"})
        self.assertEqual(payload["normalizedFilter"], {
            "type": "screen_filter",
            "action": "apply",
            "preset": "memory",
            "strength": "soft",
            "grade": {"safe": True},
        })
        self.assertEqual(payload["normalizedFilterClear"], {
            "type": "screen_filter",
            "action": "clear",
            "preset": "mono",
            "strength": "strong",
            "grade": {"safe": True},
        })
        self.assertEqual(payload["normalizedBlur"], {
            "type": "depth_blur",
            "action": "apply",
            "focus": "right",
            "strength": "strong",
        })
        self.assertEqual(payload["normalizedParticle"], {
            "type": "particle_effect",
            "action": "start",
            "preset": "snow",
            "intensity": "heavy",
            "speed": "fast",
            "density": 40,
            "normalized": True,
        })
        self.assertEqual(payload["normalizedParticleStop"], {
            "type": "particle_effect",
            "action": "stop",
            "preset": "rain",
            "intensity": "light",
            "speed": "slow",
            "density": 40,
            "normalized": True,
        })
        self.assertEqual(payload["normalizedJumpFallback"], {"type": "jump", "targetSceneId": "scene_end"})
        self.assertEqual(payload["normalizedCondition"], {
            "type": "condition",
            "branches": [
                {
                    "when": [
                        {"variableId": "affection", "operator": ">=", "value": 2},
                        {"variableId": "met", "operator": "==", "value": True},
                    ],
                    "gotoSceneId": "scene_roof",
                },
            ],
            "elseGotoSceneId": "scene_end",
        })
        self.assertIsNone(payload["normalizedConditionDropsUnknownVariable"])


if __name__ == "__main__":
    unittest.main()
