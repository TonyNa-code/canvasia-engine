from __future__ import annotations

import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

import renpy_export


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_RUNTIME_SETTINGS_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_runtime_settings.js"
FRONTEND_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "renpy_exporter.js"


def load_frontend_payload(script_body: str) -> dict:
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        const vm = require("vm");
        const context = {{ window: {{}} }};
        context.globalThis = context;
        vm.createContext(context);
        vm.runInContext(fs.readFileSync({json.dumps(str(FRONTEND_RUNTIME_SETTINGS_MODULE_PATH))}, "utf8"), context);
        vm.runInContext(fs.readFileSync({json.dumps(str(FRONTEND_MODULE_PATH))}, "utf8"), context);
        const tools = context.window.CanvasiaEditorRenpyExporter;
        {script_body}
        """
    )
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


class RenpyExportContractTests(unittest.TestCase):
    def test_frontend_and_backend_export_contracts_stay_in_sync(self) -> None:
        frontend = load_frontend_payload(
            """
            process.stdout.write(JSON.stringify(tools.getRenpyExportContract()));
            """
        )

        self.assertEqual(frontend, renpy_export.get_renpy_export_contract())

    def test_invalid_condition_operator_is_guarded_on_both_exporters(self) -> None:
        frontend = load_frontend_payload(
            """
            const warnings = [];
            const lines = tools.renderBlock({
              type: "condition",
              branches: [{
                when: [{ variableId: "affection", operator: "roughly", value: 2 }],
                gotoSceneId: "scene_good",
              }],
              elseGotoSceneId: "scene_bad",
            }, {
              warnings,
              sceneId: "scene_open",
              blockIndex: 4,
              sceneMap: new Map([
                ["scene_good", { id: "scene_good" }],
                ["scene_bad", { id: "scene_bad" }],
              ]),
            });
            process.stdout.write(JSON.stringify({ lines, warnings }));
            """
        )

        backend_warnings: list[dict] = []
        backend_expression = renpy_export.render_condition_rule_expression(
            {"variableId": "affection", "operator": "roughly", "value": 2},
            {"warnings": backend_warnings, "sceneId": "scene_open", "blockIndex": 4},
        )

        self.assertIn("if affection == 2:", "\n".join(frontend["lines"]))
        self.assertEqual(backend_expression, "affection == 2")
        self.assertEqual(frontend["warnings"][0]["code"], "renpy_condition_operator_review")
        self.assertEqual(backend_warnings[0]["code"], "renpy_condition_operator_review")

    def test_string_condition_operators_export_to_renpy_python_expressions(self) -> None:
        frontend = load_frontend_payload(
            """
            const warnings = [];
            const expressions = [
              tools.renderConditionRuleExpression({ variableId: "route", operator: "contains", value: "good" }, { warnings }),
              tools.renderConditionRuleExpression({ variableId: "route", operator: "not_contains", value: "bad" }, { warnings }),
              tools.renderConditionRuleExpression({ variableId: "route", operator: "starts_with", value: "good" }, { warnings }),
              tools.renderConditionRuleExpression({ variableId: "route", operator: "ends_with", value: "end" }, { warnings }),
            ];
            process.stdout.write(JSON.stringify({ expressions, warnings, contract: tools.getRenpyExportContract() }));
            """
        )

        backend_warnings: list[dict] = []
        backend_expressions = [
            renpy_export.render_condition_rule_expression(
                {"variableId": "route", "operator": "contains", "value": "good"},
                {"warnings": backend_warnings},
            ),
            renpy_export.render_condition_rule_expression(
                {"variableId": "route", "operator": "not_contains", "value": "bad"},
                {"warnings": backend_warnings},
            ),
            renpy_export.render_condition_rule_expression(
                {"variableId": "route", "operator": "starts_with", "value": "good"},
                {"warnings": backend_warnings},
            ),
            renpy_export.render_condition_rule_expression(
                {"variableId": "route", "operator": "ends_with", "value": "end"},
                {"warnings": backend_warnings},
            ),
        ]

        expected = [
            '"good" in str(route)',
            '"bad" not in str(route)',
            'str(route).startswith("good")',
            'str(route).endswith("end")',
        ]
        self.assertEqual(frontend["expressions"], expected)
        self.assertEqual(backend_expressions, expected)
        self.assertEqual(frontend["warnings"], [])
        self.assertEqual(backend_warnings, [])
        self.assertIn("contains", frontend["contract"]["conditionOperators"])

    def test_pop_character_transition_uses_native_renpy_zoom_transitions(self) -> None:
        frontend = load_frontend_payload(
            """
            const showWarnings = [];
            const hideWarnings = [];
            const showLines = tools.renderBlock({
              type: "character_show",
              characterId: "heroine",
              position: "center",
              transition: "pop",
              transitionDurationMs: 720,
            }, { warnings: showWarnings, sceneId: "scene_open", blockIndex: 2 });
            const hideLines = tools.renderBlock({
              type: "character_hide",
              characterId: "heroine",
              transition: "pop",
              transitionDurationMs: 720,
            }, { warnings: hideWarnings, sceneId: "scene_open", blockIndex: 8 });
            process.stdout.write(JSON.stringify({ showLines, hideLines, showWarnings, hideWarnings }));
            """
        )

        backend_show_warnings: list[dict] = []
        backend_hide_warnings: list[dict] = []
        backend_show_transition = renpy_export.get_character_transition_expression(
            {"transition": "pop", "transitionDurationMs": 720},
            {"warnings": backend_show_warnings, "sceneId": "scene_open", "blockIndex": 2},
            "show",
        )
        backend_hide_transition = renpy_export.get_character_transition_expression(
            {"transition": "pop", "transitionDurationMs": 720},
            {"warnings": backend_hide_warnings, "sceneId": "scene_open", "blockIndex": 8},
            "hide",
        )

        self.assertIn("show heroine at center with zoomin", "\n".join(frontend["showLines"]))
        self.assertIn("hide heroine with zoomout", "\n".join(frontend["hideLines"]))
        self.assertEqual(backend_show_transition, "zoomin")
        self.assertEqual(backend_hide_transition, "zoomout")
        self.assertEqual(frontend["showWarnings"], [])
        self.assertEqual(frontend["hideWarnings"], [])
        self.assertEqual(backend_show_warnings, [])
        self.assertEqual(backend_hide_warnings, [])

    def test_particle_image_asset_exports_to_snowblossom_image_on_both_exporters(self) -> None:
        frontend = load_frontend_payload(
            """
            const warnings = [];
            const lines = tools.renderBlock({
              type: "particle_effect",
              action: "start",
              preset: "snow",
              intensity: "light",
              speed: "slow",
              wind: "right",
              area: "full",
              assetId: "snowflake_ui",
              sizeMin: 16,
              sizeMax: 24,
            }, {
              warnings,
              sceneId: "scene_open",
              blockIndex: 5,
              assetMap: new Map([
                ["snowflake_ui", { id: "snowflake_ui", type: "ui", path: "ui/snowflake.png" }],
              ]),
            });
            process.stdout.write(JSON.stringify({ lines, warnings }));
            """
        )

        backend_warnings: list[dict] = []
        backend_lines = renpy_export.render_particle_block(
            {
                "type": "particle_effect",
                "action": "start",
                "preset": "snow",
                "intensity": "light",
                "speed": "slow",
                "wind": "right",
                "area": "full",
                "assetId": "snowflake_ui",
                "sizeMin": 16,
                "sizeMax": 24,
            },
            {
                "warnings": backend_warnings,
                "sceneId": "scene_open",
                "blockIndex": 5,
                "assetMap": {
                    "snowflake_ui": {"id": "snowflake_ui", "type": "ui", "path": "ui/snowflake.png"},
                },
            },
        )

        self.assertIn('SnowBlossom(Image("ui/snowflake.png")', "\n".join(frontend["lines"]))
        self.assertIn('SnowBlossom(Image("ui/snowflake.png")', "\n".join(backend_lines))
        self.assertEqual(frontend["warnings"], [])
        self.assertEqual(backend_warnings, [])

    def test_particle_non_image_asset_falls_back_with_review_warning_on_both_exporters(self) -> None:
        frontend = load_frontend_payload(
            """
            const warnings = [];
            const lines = tools.renderBlock({
              type: "particle_effect",
              action: "start",
              preset: "snow",
              assetId: "theme_bgm",
            }, {
              warnings,
              sceneId: "scene_open",
              blockIndex: 6,
              assetMap: new Map([
                ["theme_bgm", { id: "theme_bgm", type: "bgm", path: "audio/theme.ogg" }],
              ]),
            });
            process.stdout.write(JSON.stringify({ lines, warnings }));
            """
        )

        backend_warnings: list[dict] = []
        backend_lines = renpy_export.render_particle_block(
            {
                "type": "particle_effect",
                "action": "start",
                "preset": "snow",
                "assetId": "theme_bgm",
            },
            {
                "warnings": backend_warnings,
                "sceneId": "scene_open",
                "blockIndex": 6,
                "assetMap": {
                    "theme_bgm": {"id": "theme_bgm", "type": "bgm", "path": "audio/theme.ogg"},
                },
            },
        )

        self.assertIn('SnowBlossom(Text("*", color="#ffffff", size=12)', "\n".join(frontend["lines"]))
        self.assertIn('SnowBlossom(Text("*", color="#ffffff", size=12)', "\n".join(backend_lines))
        self.assertEqual(frontend["warnings"][0]["code"], "renpy_particle_asset_type_review")
        self.assertEqual(backend_warnings[0]["code"], "renpy_particle_asset_type_review")

    def test_dialog_box_config_exports_to_renpy_say_screen(self) -> None:
        bundle = {
            "project": {
                "resolution": {"width": 1920, "height": 1080},
                "dialogBoxConfig": {
                    "widthPercent": 82,
                    "minHeight": 132,
                    "backgroundColor": "#10243a",
                    "backgroundOpacity": 12,
                    "borderColor": "#6fdfff",
                    "borderOpacity": 0,
                    "textColor": "#f0f6ff",
                    "speakerColor": "#ffffff",
                    "anchor": "center",
                    "offsetXPercent": 12,
                    "offsetYPercent": -8,
                },
            }
        }

        screens = renpy_export.build_renpy_screens_file(bundle)
        summary = renpy_export.build_renpy_dialog_screen_summary(bundle)

        self.assertIn("screen say(who, what):", screens)
        self.assertIn("style canvasia_say_window is default:", screens)
        self.assertIn("    xpos 1190", screens)
        self.assertIn("    ypos 454", screens)
        self.assertIn("    yanchor 0.5", screens)
        self.assertIn("    xsize 1574", screens)
        self.assertIn("    yminimum 132", screens)
        self.assertIn('    background "#10243a1f"', screens)
        self.assertIn('    color "#f0f6ff"', screens)
        self.assertEqual(summary["anchor"], "center")
        self.assertEqual(summary["borderColor"], "#6fdfff00")

    def test_dialog_box_panel_asset_exports_to_renpy_frame_background(self) -> None:
        bundle = {
            "project": {
                "resolution": {"width": 1920, "height": 1080},
                "dialogBoxConfig": {
                    "panelAssetId": "dialog_panel",
                    "panelAssetFit": "contain",
                },
                "gameUiConfig": {
                    "fontStyle": "serif",
                    "fontFamily": "Story Serif",
                    "fontAssetId": "font_story",
                },
            }
        }
        assets_doc = {
            "assets": [
                {
                    "id": "dialog_panel",
                    "type": "ui",
                    "exportUrl": "assets/ui/dialog_panel.png",
                },
                {
                    "id": "font_story",
                    "type": "font",
                    "exportUrl": "assets/font/story.ttf",
                }
            ]
        }

        screens = renpy_export.build_renpy_screens_file(bundle, assets_doc)
        summary = renpy_export.build_renpy_dialog_screen_summary(bundle, assets_doc)

        self.assertIn('background Frame("assets/ui/dialog_panel.png", 24, 24, 24, 24)', screens)
        self.assertIn("panel=assets/ui/dialog_panel.png", screens)
        self.assertIn('    font "assets/font/story.ttf"', screens)
        self.assertIn("font=assets/font/story.ttf", screens)
        self.assertEqual(summary["panelAssetPath"], "assets/ui/dialog_panel.png")
        self.assertEqual(summary["panelAssetFit"], "contain")
        self.assertEqual(summary["fontAssetPath"], "assets/font/story.ttf")
        self.assertEqual(summary["fontFamily"], "Story Serif")

    def test_project_runtime_defaults_feed_renpy_draft_exporters(self) -> None:
        frontend = load_frontend_payload(
            """
            const data = {
              project: {
                title: "Runtime Defaults Demo",
                runtimeSettings: {
                  defaultTextSpeed: "fast",
                  defaultBgmVolume: 64,
                  defaultSfxVolume: 77,
                  defaultVoiceVolume: 88,
                  defaultVoiceEnabled: false,
                  formalSaveSlotCount: 60,
                },
              },
              assetList: [
                { id: "bgm_theme", type: "bgm", path: "audio/theme.ogg" },
                { id: "sfx_bell", type: "sfx", path: "audio/bell.ogg" },
              ],
              characters: [{ id: "hero", displayName: "Hero" }],
              chapters: [{
                name: "Opening",
                scenes: [{
                  id: "scene_open",
                  blocks: [
                    { type: "music_play", assetId: "bgm_theme", loop: true },
                    { type: "dialogue", speakerId: "hero", text: "The project default speed is active." },
                    { type: "sfx_play", assetId: "sfx_bell" },
                  ],
                }],
              }],
            };
            process.stdout.write(JSON.stringify(tools.buildRenpyDraftExport(data)));
            """
        )

        bundle = {
            "project": {
                "title": "Runtime Defaults Demo",
                "runtimeSettings": {
                    "defaultTextSpeed": "fast",
                    "defaultBgmVolume": 64,
                    "defaultSfxVolume": 77,
                    "defaultVoiceVolume": 88,
                    "defaultVoiceDuckingRatio": 35,
                    "defaultVoiceEnabled": False,
                    "formalSaveSlotCount": 60,
                },
            },
            "characters": {"characters": [{"id": "hero", "displayName": "Hero"}]},
            "chapters": [
                {
                    "name": "Opening",
                    "scenes": [
                        {
                            "id": "scene_open",
                            "blocks": [
                                {"type": "music_play", "assetId": "bgm_theme", "loop": True},
                                {"type": "dialogue", "speakerId": "hero", "text": "The project default speed is active."},
                                {"type": "sfx_play", "assetId": "sfx_bell"},
                            ],
                        }
                    ],
                }
            ],
        }
        assets_doc = {
            "assets": [
                {"id": "bgm_theme", "type": "bgm", "exportUrl": "audio/theme.ogg"},
                {"id": "sfx_bell", "type": "sfx", "exportUrl": "audio/bell.ogg"},
            ]
        }

        backend = renpy_export.build_renpy_draft_export(bundle, assets_doc)
        options = renpy_export.build_renpy_options_file(bundle)

        for script in (frontend["script"], backend["script"]):
            self.assertIn('play music "audio/theme.ogg" loop volume 0.64', script)
            self.assertIn('hero "{cps=72}The project default speed is active.{/cps}"', script)
            self.assertIn('play sound "audio/bell.ogg" volume 0.77', script)

        self.assertEqual(frontend["runtimeSettings"]["defaultTextSpeed"], "fast")
        self.assertEqual(backend["runtimeSettings"]["defaultBgmVolume"], 64)
        self.assertEqual(backend["runtimeSettings"]["defaultVoiceDuckingRatio"], 35)
        self.assertIn('define canvasia_default_text_speed = "fast"', options)
        self.assertIn("define canvasia_default_text_cps = 72", options)
        self.assertIn("define canvasia_default_music_volume = 0.64", options)
        self.assertIn("define canvasia_default_sound_volume = 0.77", options)
        self.assertIn("define canvasia_default_voice_volume = 0.88", options)
        self.assertIn("define canvasia_voice_enabled = False", options)
        self.assertIn("define canvasia_voice_ducking_enabled = True", options)
        self.assertIn("define canvasia_voice_ducking_ratio = 0.35", options)
        self.assertIn("define canvasia_formal_save_slot_count = 60", options)
        self.assertIn("default preferences.text_cps = 72", options)
        self.assertIn("default preferences.volume.music = 0.64", options)
        self.assertIn("default preferences.volume.sfx = 0.77", options)
        self.assertIn("default preferences.volume.voice = 0", options)

        instant_options = renpy_export.build_renpy_options_file(
            {"project": {"runtimeSettings": {"defaultTextSpeed": "instant", "defaultVoiceEnabled": True, "defaultVoiceVolume": 88}}}
        )
        self.assertIn("default preferences.text_cps = 0", instant_options)
        self.assertIn("default preferences.volume.voice = 0.88", instant_options)

    def test_renpy_quality_report_blocks_missing_runtime_preferences(self) -> None:
        bundle = {
            "project": {
                "title": "Runtime Quality Demo",
                "runtimeSettings": {
                    "defaultTextSpeed": "fast",
                    "defaultBgmVolume": 64,
                    "defaultSfxVolume": 77,
                    "defaultVoiceVolume": 88,
                    "defaultVoiceEnabled": False,
                    "formalSaveSlotCount": 60,
                },
            }
        }
        export_result = {
            "sceneCount": 1,
            "runtimeSettings": bundle["project"]["runtimeSettings"],
            "warnings": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir)
            game_dir = build_dir / renpy_export.RENPY_GAME_DIR_NAME
            game_dir.mkdir()
            (game_dir / renpy_export.RENPY_SCRIPT_FILE_NAME).write_text("label start:\n    return\n", encoding="utf-8")
            (game_dir / renpy_export.RENPY_SCREENS_FILE_NAME).write_text(
                "screen say(who, what):\n    text what\n\nstyle canvasia_say_window is default:\n    pass\n",
                encoding="utf-8",
            )
            options_path = game_dir / renpy_export.RENPY_OPTIONS_FILE_NAME
            options = renpy_export.build_renpy_options_file(bundle)
            options_path.write_text(options, encoding="utf-8")

            report = renpy_export.build_renpy_quality_report(build_dir, export_result)
            self.assertEqual(report["status"], "ready")
            self.assertGreaterEqual(report["summary"]["runtimePreferenceCount"], 10)
            self.assertEqual(report["summary"]["missingRuntimePreferenceCount"], 0)
            self.assertTrue(report["summary"]["optionsPresent"])

            options_path.write_text(options.replace("default preferences.volume.voice = 0\n", ""), encoding="utf-8")
            broken_report = renpy_export.build_renpy_quality_report(build_dir, export_result)
            self.assertEqual(broken_report["status"], "blocked")
            self.assertEqual(broken_report["summary"]["missingRuntimePreferenceCount"], 1)
            self.assertTrue(
                any(issue["code"] == "renpy_missing_runtime_preference" for issue in broken_report["issues"])
            )


if __name__ == "__main__":
    unittest.main()
