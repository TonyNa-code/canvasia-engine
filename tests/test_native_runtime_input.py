from __future__ import annotations

import unittest
from pathlib import Path

from native_runtime.runtime_input import (
    CONTROLLER_REPEAT_DELAY_MS,
    CONTROLLER_REPEAT_INTERVAL_MS,
    build_controller_control_group,
    build_controller_input_state,
    build_controller_status,
    get_controller_action_key_attr,
    get_controller_repeat_actions,
    translate_controller_input,
)


ROOT_DIR = Path(__file__).resolve().parents[1]


class NativeRuntimeInputTests(unittest.TestCase):
    def test_buttons_map_to_mature_visual_novel_actions(self) -> None:
        expected = {
            0: "confirm",
            1: "back",
            2: "history",
            3: "system",
            4: "rollback",
            5: "auto",
            6: "skip",
            7: "system",
            12: "up",
            13: "down",
            14: "left",
            15: "right",
        }
        for button, action in expected.items():
            result = translate_controller_input("button_down", button=button)
            self.assertEqual(result["actions"], [action])
        self.assertEqual(translate_controller_input("button_down", button=99)["actions"], [])

    def test_axis_motion_events_do_not_duplicate_before_recentering(self) -> None:
        state = build_controller_input_state()
        first = translate_controller_input("axis_motion", axis=0, axis_value=0.8, state=state)
        held = translate_controller_input("axis_motion", axis=0, axis_value=0.9, state=first["state"])
        centered = translate_controller_input("axis_motion", axis=0, axis_value=0.0, state=held["state"])
        repeated = translate_controller_input("axis_motion", axis=0, axis_value=0.75, state=centered["state"])

        self.assertEqual(first["actions"], ["right"])
        self.assertEqual(held["actions"], [])
        self.assertEqual(centered["actions"], [])
        self.assertEqual(repeated["actions"], ["right"])

    def test_direction_hold_repeats_after_delay_and_stops_on_release(self) -> None:
        first = translate_controller_input("axis_motion", axis=0, axis_value=0.8, now_ms=100)
        before_delay = get_controller_repeat_actions(first["state"], now_ms=519)
        first_repeat = get_controller_repeat_actions(before_delay["state"], now_ms=520)
        too_soon = get_controller_repeat_actions(first_repeat["state"], now_ms=600)
        second_repeat = get_controller_repeat_actions(too_soon["state"], now_ms=615)
        released = translate_controller_input(
            "axis_motion",
            axis=0,
            axis_value=0.0,
            state=second_repeat["state"],
            now_ms=700,
        )
        after_release = get_controller_repeat_actions(released["state"], now_ms=1200)

        self.assertEqual(first["actions"], ["right"])
        self.assertEqual(before_delay["actions"], [])
        self.assertEqual(first_repeat["actions"], ["right"])
        self.assertEqual(too_soon["actions"], [])
        self.assertEqual(second_repeat["actions"], ["right"])
        self.assertEqual(released["actions"], [])
        self.assertEqual(after_release["actions"], [])
        self.assertEqual(CONTROLLER_REPEAT_DELAY_MS, 420)
        self.assertEqual(CONTROLLER_REPEAT_INTERVAL_MS, 95)

    def test_dpad_buttons_repeat_without_repeating_confirm(self) -> None:
        direction = translate_controller_input("button_down", button=15, now_ms=0)
        held = get_controller_repeat_actions(direction["state"], now_ms=420)
        released = translate_controller_input(
            "button_up",
            button=15,
            state=held["state"],
            now_ms=500,
        )
        confirm = translate_controller_input("button_down", button=0, state=released["state"], now_ms=600)
        confirm_held = get_controller_repeat_actions(confirm["state"], now_ms=2000)

        self.assertEqual(direction["actions"], ["right"])
        self.assertEqual(held["actions"], ["right"])
        self.assertEqual(released["actions"], [])
        self.assertEqual(confirm["actions"], ["confirm"])
        self.assertEqual(confirm_held["actions"], [])

    def test_hat_supports_diagonal_navigation_without_repeat_noise(self) -> None:
        first = translate_controller_input("hat_motion", hat=0, hat_value=(1, 1))
        held = translate_controller_input("hat_motion", hat=0, hat_value=(1, 1), state=first["state"])
        released = translate_controller_input("hat_motion", hat=0, hat_value=(0, 0), state=held["state"])

        self.assertEqual(first["actions"], ["right", "up"])
        self.assertEqual(held["actions"], [])
        self.assertEqual(released["actions"], [])

    def test_status_and_help_are_safe_for_user_facing_surfaces(self) -> None:
        empty = build_controller_status([])
        connected = build_controller_status(["Wireless Controller", "Gamepad" * 30])
        group = build_controller_control_group()

        self.assertFalse(empty["connected"])
        self.assertEqual(empty["label"], "未连接")
        self.assertTrue(connected["connected"])
        self.assertEqual(connected["connectedCount"], 2)
        self.assertLessEqual(len(connected["names"][1]), 80)
        self.assertEqual(group["key"], "controller")
        self.assertEqual(len(group["controls"]), 4)
        self.assertIn("按住可连续移动", group["controls"][0]["detail"])
        self.assertEqual(get_controller_action_key_attr("confirm"), "K_RETURN")
        self.assertIsNone(get_controller_action_key_attr("unknown"))

    def test_native_player_polls_controller_repeat_each_frame(self) -> None:
        source = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")

        self.assertIn("get_controller_repeat_actions,", source)
        self.assertIn('event_kind = "button_up"', source)
        self.assertIn("def handle_controller_repeat(self, now_ms: object | None = None) -> bool:", source)
        self.assertIn("running = self.handle_controller_repeat()", source)


if __name__ == "__main__":
    unittest.main()
