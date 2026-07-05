from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

import renpy_export


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "renpy_exporter.js"


def load_frontend_payload(script_body: str) -> dict:
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        const vm = require("vm");
        const context = {{ window: {{}} }};
        context.globalThis = context;
        vm.createContext(context);
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
                when: [{ variableId: "affection", operator: "contains", value: 2 }],
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
            {"variableId": "affection", "operator": "contains", "value": 2},
            {"warnings": backend_warnings, "sceneId": "scene_open", "blockIndex": 4},
        )

        self.assertIn("if affection == 2:", "\n".join(frontend["lines"]))
        self.assertEqual(backend_expression, "affection == 2")
        self.assertEqual(frontend["warnings"][0]["code"], "renpy_condition_operator_review")
        self.assertEqual(backend_warnings[0]["code"], "renpy_condition_operator_review")

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


if __name__ == "__main__":
    unittest.main()
