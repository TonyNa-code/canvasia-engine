from __future__ import annotations

import unittest

from native_runtime.runtime_input import (
    build_controller_control_group,
    build_controller_input_state,
    build_controller_status,
    get_controller_action_key_attr,
    translate_controller_input,
)


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
        }
        for button, action in expected.items():
            result = translate_controller_input("button_down", button=button)
            self.assertEqual(result["actions"], [action])
        self.assertEqual(translate_controller_input("button_down", button=99)["actions"], [])

    def test_axis_navigation_requires_recentering_before_repeating(self) -> None:
        state = build_controller_input_state()
        first = translate_controller_input("axis_motion", axis=0, axis_value=0.8, state=state)
        held = translate_controller_input("axis_motion", axis=0, axis_value=0.9, state=first["state"])
        centered = translate_controller_input("axis_motion", axis=0, axis_value=0.0, state=held["state"])
        repeated = translate_controller_input("axis_motion", axis=0, axis_value=0.75, state=centered["state"])

        self.assertEqual(first["actions"], ["right"])
        self.assertEqual(held["actions"], [])
        self.assertEqual(centered["actions"], [])
        self.assertEqual(repeated["actions"], ["right"])

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
        self.assertEqual(get_controller_action_key_attr("confirm"), "K_RETURN")
        self.assertIsNone(get_controller_action_key_attr("unknown"))


if __name__ == "__main__":
    unittest.main()
