from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

import renpy_export
import run_editor
from native_runtime.runtime_story_text import parse_runtime_story_text


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_story_text.js"


def normalize_plan(plan: dict) -> dict:
    text = str(plan.get("plainText") or "")
    cues = []
    for cue in plan.get("cues") or []:
        index = int(cue.get("index") or 0)
        normalized = {"before": text[:index], "type": cue.get("type")}
        if cue.get("pauseMs") is not None:
            normalized["pauseMs"] = cue.get("pauseMs")
        if cue.get("speed") is not None:
            normalized["speed"] = cue.get("speed")
        cues.append(normalized)
    segments = []
    for segment in plan.get("segments") or []:
        start = int(segment.get("start") or 0)
        end = int(segment.get("end") or start)
        normalized = {
            "text": text[start:end],
            "type": segment.get("type"),
        }
        if segment.get("annotation") is not None:
            normalized["annotation"] = segment.get("annotation")
        if segment.get("color") is not None:
            normalized["color"] = segment.get("color")
        segments.append(normalized)
    return {"plainText": text, "cues": cues, "segments": segments}


class StoryTextContractTests(unittest.TestCase):
    def test_web_and_native_share_visible_rich_text_semantics(self) -> None:
        fixtures = [
            "她说[[em=等等]][[pause=0.35]][[ruby=漢字|かんじ]]。",
            "A💙[[color=#FF6699|心动]][[whisper=轻声]][[speed=slow]]结束",
            "保留[[color=red|文字]]和[[ruby=字|]]",
        ]
        script = textwrap.dedent(
            f"""
            import {{ parseRuntimeStoryText }} from {json.dumps(WEB_MODULE_PATH.as_uri())};
            const fixtures = {json.dumps(fixtures, ensure_ascii=False)};
            const normalized = fixtures.map((value) => {{
              const plan = parseRuntimeStoryText(value);
              return {{
                plainText: plan.plainText,
                cues: plan.cues.map((cue) => ({{
                  before: plan.plainText.slice(0, cue.index),
                  type: cue.type,
                  pauseMs: cue.pauseMs,
                  speed: cue.speed,
                }})),
                segments: plan.segments.map((segment) => ({{
                  text: plan.plainText.slice(segment.start, segment.end),
                  type: segment.type,
                  annotation: segment.annotation,
                  color: segment.color,
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
        native_plans = [normalize_plan(parse_runtime_story_text(value)) for value in fixtures]
        self.assertEqual(web_plans, native_plans)

    def test_renpy_export_preserves_rich_text_and_inline_pacing(self) -> None:
        rendered = renpy_export.render_renpy_text(
            {
                "type": "dialogue",
                "textSpeed": "fast",
                "text": "[[em=重要]][[pause=0.35]][[ruby=漢字|かんじ]][[color=#ff6699|心动]][[whisper=轻声]]",
            },
            {"runtimeSettings": {}, "variableMap": {}},
        )

        self.assertIn("{b}重要{/b}", rendered)
        self.assertIn("{w=0.35}", rendered)
        self.assertIn("{rb}漢字{/rb}{rt}かんじ{/rt}", rendered)
        self.assertIn("{color=#ff6699}心动{/color}", rendered)
        self.assertIn("{i}{size=-3}{alpha=0.82}轻声{/alpha}{/size}{/i}", rendered)

    def test_editor_runtimes_and_packages_include_story_text_modules(self) -> None:
        editor_index = (ROOT_DIR / "prototype_editor" / "index.html").read_text(encoding="utf-8")
        editor_app = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")
        player_source = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        native_player_source = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        native_layout_source = (
            ROOT_DIR / "native_runtime" / "runtime_dialogue_layouts.py"
        ).read_text(encoding="utf-8")

        for script_name in ("runtime_rich_text.js", "runtime_story_text.js"):
            self.assertIn(script_name, run_editor.EXPORT_PLAYER_SCRIPT_FILES)
            self.assertIn(f"../export_player_template/{script_name}", editor_index)
        native_module_names = [
            name for _source, name in run_editor.NATIVE_RUNTIME_REQUIRED_MODULE_FILES
        ]
        for module_name in (
            run_editor.NATIVE_RUNTIME_RICH_TEXT_NAME,
            run_editor.NATIVE_RUNTIME_STORY_TEXT_NAME,
            run_editor.NATIVE_RUNTIME_RICH_TEXT_RENDERER_NAME,
        ):
            self.assertIn(module_name, native_module_names)
        self.assertIn("./modules/rich_text_editor.js", editor_index)
        self.assertIn('action === "insert-rich-text"', editor_app)
        self.assertIn('from "./runtime_story_text.js"', player_source)
        self.assertIn("runtime_story_text import", native_player_source)
        self.assertIn("runtime_rich_text_renderer import", native_layout_source)


if __name__ == "__main__":
    unittest.main()
