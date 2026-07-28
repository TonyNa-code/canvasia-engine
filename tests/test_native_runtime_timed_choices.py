from __future__ import annotations

import unittest

from native_runtime.runtime_timed_choices import (
    NativeTimedChoiceController,
    build_native_timed_choice_presentation,
    resolve_timed_choice_target,
    sanitize_timed_choice_config,
    sanitize_timed_choice_state,
)


class NativeRuntimeTimedChoicesTests(unittest.TestCase):
    def test_config_target_and_persisted_state_are_sanitized(self) -> None:
        disabled = sanitize_timed_choice_config({"timeoutSeconds": 0})
        minimum = sanitize_timed_choice_config({"timeoutSeconds": 0.2})
        maximum = sanitize_timed_choice_config(
            {"choiceTimeoutSeconds": 900, "choiceTimeoutOptionId": " locked "}
        )
        options = [
            {"id": "hidden", "choiceVisible": False},
            {"id": "locked", "choiceEnabled": False},
            {"id": "safe", "choiceEnabled": True},
        ]
        target = resolve_timed_choice_target(options, "locked")
        state = sanitize_timed_choice_state(
            {
                "choiceKey": " scene:choice ",
                "targetOptionId": " safe ",
                "remainingMs": 999999,
            },
            {"timeoutSeconds": 12},
        )

        self.assertFalse(disabled["enabled"])
        self.assertEqual(minimum["timeoutSeconds"], 1)
        self.assertEqual(maximum["timeoutSeconds"], 300)
        self.assertEqual(maximum["timeoutOptionId"], "locked")
        self.assertEqual(target, "safe")
        self.assertEqual(state["choiceKey"], "scene:choice")
        self.assertEqual(state["remainingMs"], 12000)

    def test_controller_pauses_resumes_and_times_out_once(self) -> None:
        controller = NativeTimedChoiceController()
        started = controller.start(
            choice_key="scene:choice",
            block={"timeoutSeconds": 10, "timeoutOptionId": "locked"},
            choice_options=[
                {"id": "locked", "choiceEnabled": False},
                {"id": "safe", "choiceEnabled": True},
            ],
            now_ms=0,
        )
        before_pause = controller.snapshot(2500)
        paused = controller.set_paused(True, 2500)
        while_paused = controller.snapshot(8000)
        resumed = controller.set_paused(False, 8000)
        timeout_target = controller.update(15500)
        repeated_target = controller.update(18000)
        expired = controller.snapshot(18000)

        self.assertEqual(started["targetOptionId"], "safe")
        self.assertEqual(before_pause["remainingMs"], 7500)
        self.assertTrue(paused["paused"])
        self.assertEqual(while_paused["remainingMs"], 7500)
        self.assertFalse(resumed["paused"])
        self.assertEqual(timeout_target, "safe")
        self.assertEqual(repeated_target, "")
        self.assertFalse(expired["active"])
        self.assertTrue(expired["expired"])
        self.assertEqual(controller.serialize(18000)["remainingMs"], 0)

        restored_expired = NativeTimedChoiceController()
        restored_expired.start(
            choice_key="scene:choice",
            block={"timeoutSeconds": 10},
            choice_options=[{"id": "safe", "choiceEnabled": True}],
            now_ms=20000,
            remaining_ms=0,
        )
        self.assertEqual(restored_expired.update(20000), "safe")
        self.assertEqual(restored_expired.update(20001), "")

    def test_presentation_keeps_author_target_visible(self) -> None:
        presentation = build_native_timed_choice_presentation(
            {
                "active": True,
                "paused": True,
                "targetOptionId": "route_b",
                "durationMs": 10000,
                "remainingMs": 4200,
                "progress": 0.58,
            },
            [{"id": "route_b", "text": "追上她"}],
        )

        self.assertTrue(presentation["visible"])
        self.assertTrue(presentation["paused"])
        self.assertEqual(presentation["remainingLabel"], "4.2 秒")
        self.assertEqual(presentation["targetLabel"], "追上她")
        self.assertEqual(presentation["progress"], 0.58)


if __name__ == "__main__":
    unittest.main()
