from __future__ import annotations

import unittest

from native_runtime.runtime_text_pacing import (
    build_text_pacing_summary,
    get_initial_text_pacing_index,
    get_native_text_pacing_step_delay_ms,
    get_next_text_pacing_index,
    get_text_pacing_speed_at,
    parse_runtime_text_pacing,
    strip_runtime_text_pacing,
)


class NativeRuntimeTextPacingTests(unittest.TestCase):
    def test_parser_keeps_unknown_markers_and_strips_supported_cues(self) -> None:
        plan = parse_runtime_text_pacing(
            "A[[pause=0.35]]BC[[speed=slow]]慢慢[[speed=inherit]]结束"
        )
        invalid = parse_runtime_text_pacing("保留[[pause=oops]]和[[speed=turbo]]")

        self.assertEqual(plan["plainText"], "ABC慢慢结束")
        self.assertEqual([cue["type"] for cue in plan["cues"]], ["pause", "speed", "speed"])
        self.assertEqual(strip_runtime_text_pacing(plan["sourceText"]), plan["plainText"])
        self.assertIn("[[pause=oops]]", invalid["plainText"])
        self.assertIn("[[speed=turbo]]", invalid["plainText"])
        self.assertEqual(build_text_pacing_summary(plan["sourceText"])["pauseCount"], 1)

    def test_cue_boundaries_speed_and_player_instant_override(self) -> None:
        plan = parse_runtime_text_pacing(
            "A[[pause=0.35]]BC[[speed=slow]]慢慢[[speed=inherit]]结束"
        )
        leading = parse_runtime_text_pacing("[[pause=0.8]]开场")
        local_instant = parse_runtime_text_pacing(
            "A[[speed=instant]][[pause=0.35]]B"
        )

        self.assertEqual(get_next_text_pacing_index(plan, 0, lambda _text, index: index + 3), 1)
        self.assertEqual(get_initial_text_pacing_index(leading, lambda _text, index: index + 1), 0)
        self.assertEqual(get_text_pacing_speed_at(plan, 3, "normal"), "slow")
        self.assertEqual(get_text_pacing_speed_at(plan, 5, "normal"), "normal")
        self.assertEqual(
            get_native_text_pacing_step_delay_ms(plan, 1, "normal", "A", plan["plainText"]),
            374,
        )
        self.assertEqual(
            get_native_text_pacing_step_delay_ms(plan, 1, "instant", "A", plan["plainText"]),
            0,
        )
        self.assertEqual(
            get_native_text_pacing_step_delay_ms(
                local_instant,
                1,
                "normal",
                "A",
                local_instant["plainText"],
            ),
            350,
        )
        self.assertEqual(
            get_native_text_pacing_step_delay_ms(
                local_instant,
                1,
                "instant",
                "A",
                local_instant["plainText"],
            ),
            0,
        )


if __name__ == "__main__":
    unittest.main()
