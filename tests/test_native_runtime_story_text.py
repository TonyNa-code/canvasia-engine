from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_rich_text import (
    build_runtime_rich_text_summary,
    parse_runtime_rich_text,
)
from native_runtime.runtime_rich_text_renderer import (
    layout_runtime_rich_text,
    limit_runtime_rich_text_layout,
)
from native_runtime.runtime_story_text import (
    parse_runtime_story_text,
    strip_runtime_story_text,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_story_text.js"


class FakeFont:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def size(self, text: str) -> tuple[int, int]:
        return (len(str(text or "")) * self.width, self.height)

    def get_height(self) -> int:
        return self.height


class NativeRuntimeStoryTextTests(unittest.TestCase):
    def test_parser_matches_web_visible_text_and_cue_boundaries(self) -> None:
        fixtures = [
            "先[[em=重要]][[pause=0.35]]再[[ruby=漢字|かんじ]]",
            "[[color=#FF6699|心动]][[whisper=轻声]][[speed=slow]]结束",
            "保留[[color=red|文字]]和[[ruby=字|]]",
        ]
        native_plans = [parse_runtime_story_text(value) for value in fixtures]
        script = textwrap.dedent(
            f"""
            import {{ parseRuntimeStoryText }} from {json.dumps(WEB_MODULE_PATH.as_uri())};
            const fixtures = {json.dumps(fixtures, ensure_ascii=False)};
            process.stdout.write(JSON.stringify(fixtures.map(parseRuntimeStoryText)));
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
        for native, web in zip(native_plans, web_plans, strict=True):
            self.assertEqual(native["plainText"], web["plainText"])
            self.assertEqual(native["cues"], web["cues"])
            self.assertEqual(native["segments"], web["segments"])
        self.assertEqual(strip_runtime_story_text(fixtures[0]), "先重要再漢字")
        self.assertIn("[[color=red|文字]]", native_plans[2]["plainText"])
        self.assertEqual(build_runtime_rich_text_summary(fixtures[1])["whisper"], 1)

    def test_layout_keeps_completed_ruby_atomic_and_supports_truncation(self) -> None:
        plan = parse_runtime_story_text("开场[[ruby=漢字|かんじ]]然后[[em=强调]]结束")
        normal = FakeFont(10, 24)
        bold = FakeFont(11, 24)
        ruby = FakeFont(5, 12)
        layout = layout_runtime_rich_text(
            plan,
            normal,
            bold,
            ruby,
            70,
            (240, 244, 255),
        )
        limited = limit_runtime_rich_text_layout(layout, 2, normal, append_ellipsis=True)
        ruby_units = [
            unit
            for line in layout["lines"]
            for unit in line["units"]
            if unit.get("isRuby")
        ]

        self.assertGreater(layout["lineCount"], 1)
        self.assertEqual(len(ruby_units), 1)
        self.assertEqual(ruby_units[0]["text"], "漢字")
        self.assertEqual(ruby_units[0]["annotation"], "かんじ")
        self.assertLessEqual(limited["lineCount"], 2)
        self.assertEqual(limited["truncated"], layout["lineCount"] > 2)


if __name__ == "__main__":
    unittest.main()
