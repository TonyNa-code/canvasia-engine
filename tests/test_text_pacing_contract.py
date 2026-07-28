from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

import renpy_export
import run_editor
from native_runtime.runtime_text_pacing import parse_runtime_text_pacing


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_text_pacing.js"


def normalize_plan(plan: dict) -> dict:
    text = str(plan.get("plainText") or "")
    cues = []
    for cue in plan.get("cues") or []:
        index = int(cue.get("index") or 0)
        normalized_cue = {
            "before": text[:index],
            "type": cue.get("type"),
        }
        if cue.get("pauseMs") is not None:
            normalized_cue["pauseMs"] = cue.get("pauseMs")
        if cue.get("speed") is not None:
            normalized_cue["speed"] = cue.get("speed")
        cues.append(normalized_cue)
    return {"plainText": text, "cues": cues}


class TextPacingContractTests(unittest.TestCase):
    def test_web_and_native_parsers_share_visible_semantics(self) -> None:
        fixtures = [
            "她说[[pause=0.35]]等等[[speed=slow]]慢一点[[speed=inherit]]。",
            "A💙[[pause=0.8]]B[[speed=fast]]C[[speed=inherit]]D",
            "保留[[pause=oops]]和[[speed=turbo]]",
        ]
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(WEB_MODULE_PATH.as_uri())};
            const fixtures = {json.dumps(fixtures, ensure_ascii=False)};
            const normalized = fixtures.map((value) => {{
              const plan = tools.parseRuntimeTextPacing(value);
              return {{
                plainText: plan.plainText,
                cues: plan.cues.map((cue) => ({{
                  before: plan.plainText.slice(0, cue.index),
                  type: cue.type,
                  pauseMs: cue.pauseMs,
                  speed: cue.speed,
                }})),
              }};
            }});
            process.stdout.write(JSON.stringify(normalized));
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
        web_plans = json.loads(completed.stdout)
        native_plans = [normalize_plan(parse_runtime_text_pacing(value)) for value in fixtures]
        self.assertEqual(web_plans, native_plans)

    def test_renpy_export_preserves_inline_waits_and_speed_changes(self) -> None:
        rendered = renpy_export.render_renpy_text(
            {
                "type": "dialogue",
                "textSpeed": "fast",
                "text": "她说[[pause=0.35]]等等[[speed=slow]]慢一点[[speed=inherit]]。",
            },
            {"runtimeSettings": {}, "variableMap": {}},
        )

        self.assertEqual(
            rendered,
            "{cps=72}她说{w=0.35}等等{/cps}{cps=24}慢一点{/cps}{cps=72}。{/cps}",
        )

    def test_editor_runtime_and_packaging_contract_include_pacing_modules(self) -> None:
        editor_index = (ROOT_DIR / "prototype_editor" / "index.html").read_text(encoding="utf-8")
        player_source = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        native_source = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        renpy_frontend_source = (
            ROOT_DIR / "prototype_editor" / "modules" / "renpy_exporter.js"
        ).read_text(encoding="utf-8")

        self.assertIn("runtime_text_pacing.js", run_editor.EXPORT_PLAYER_SCRIPT_FILES)
        self.assertIn(
            run_editor.NATIVE_RUNTIME_TEXT_PACING_NAME,
            [name for _source, name in run_editor.NATIVE_RUNTIME_REQUIRED_MODULE_FILES],
        )
        self.assertIn("../export_player_template/runtime_text_pacing.js", editor_index)
        self.assertIn("./modules/text_pacing_editor.js", editor_index)
        self.assertIn('from "./runtime_text_pacing.js"', player_source)
        self.assertIn("runtime_text_pacing import", native_source)
        self.assertIn("build_current_story_line", native_source)
        self.assertIn("global.CanvasiaRuntimeTextPacing.parseRuntimeTextPacing", renpy_frontend_source)
        self.assertNotIn("const runtimeTextPacingTools = global.CanvasiaRuntimeTextPacing", renpy_frontend_source)


if __name__ == "__main__":
    unittest.main()
