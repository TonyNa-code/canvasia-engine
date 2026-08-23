from __future__ import annotations

import unittest
from types import SimpleNamespace

from native_runtime.runtime_playback_lifecycle import (
    NativePlaybackLifecycleController,
    shift_deadline_ms,
    shift_record_timestamp,
    shift_timestamp_ms,
)
from native_runtime.runtime_player import NativeRuntimePlayer


class NativeRuntimePlaybackLifecycleTests(unittest.TestCase):
    def test_controller_reports_single_suspend_resume_transition_and_background_fps(self) -> None:
        controller = NativePlaybackLifecycleController(background_fps=9)

        active = controller.update(True, 100)
        suspended = controller.update(False, 250)
        still_suspended = controller.update(False, 900)
        resumed = controller.update(True, 1250)

        self.assertEqual(active["event"], "none")
        self.assertEqual(suspended["event"], "suspend")
        self.assertTrue(still_suspended["suspended"])
        self.assertEqual(still_suspended["currentSuspendedDurationMs"], 650)
        self.assertEqual(controller.get_target_fps(60), 60)
        self.assertEqual(resumed["event"], "resume")
        self.assertEqual(resumed["lastSuspendedDurationMs"], 1000)
        self.assertEqual(resumed["totalSuspendedMs"], 1000)

        controller.update(False, 1400)
        self.assertEqual(controller.get_target_fps(60), 9)

    def test_resume_shift_helpers_preserve_zero_and_move_active_timestamps(self) -> None:
        record = {"startedAtMs": 500, "label": "motion"}

        self.assertEqual(shift_deadline_ms(0, 800), 0)
        self.assertEqual(shift_deadline_ms(1200, 800), 2000)
        self.assertEqual(shift_timestamp_ms(500, 800), 1300)
        self.assertTrue(shift_record_timestamp(record, 800))
        self.assertEqual(record["startedAtMs"], 1300)
        self.assertFalse(shift_record_timestamp({"label": "none"}, 800))

    def test_native_player_shifts_every_active_story_clock_on_resume(self) -> None:
        player = NativeRuntimePlayer.__new__(NativeRuntimePlayer)
        player.auto_play_deadline_ms = 1200
        player.skip_deadline_ms = 1300
        player.current_line_started_at_ms = 200
        player.current_line_next_reveal_at_ms = 900
        player.profile_session_started_at_ms = 100
        player.background_transition = {"startedAtMs": 300}
        player.character_motions = {"hero": {"startedAtMs": 320}}
        player.stage_image_motions = {"prop": {"startedAtMs": 340}}
        player.visible_characters = {"hero": {"transition": {"startedAtMs": 360}}}
        player.leaving_characters = {"friend": {"transition": {"startedAtMs": 380}}}
        player.current_line = {"type": "credits_roll", "creditsPlayback": {"startedAtMs": 400}}
        player.achievement_notification = {"expiresAtMs": 2400}
        player.speaker_focus_controller = SimpleNamespace(transition_started_at_ms=420)
        player.dialogue_camera_controller = SimpleNamespace(transition_started_at_ms=440)

        player.shift_runtime_playback_timestamps(600)

        self.assertEqual(player.auto_play_deadline_ms, 1800)
        self.assertEqual(player.skip_deadline_ms, 1900)
        self.assertEqual(player.current_line_next_reveal_at_ms, 1500)
        self.assertEqual(player.background_transition["startedAtMs"], 900)
        self.assertEqual(player.character_motions["hero"]["startedAtMs"], 920)
        self.assertEqual(player.stage_image_motions["prop"]["startedAtMs"], 940)
        self.assertEqual(player.visible_characters["hero"]["transition"]["startedAtMs"], 960)
        self.assertEqual(player.leaving_characters["friend"]["transition"]["startedAtMs"], 980)
        self.assertEqual(player.current_line["creditsPlayback"]["startedAtMs"], 1000)
        self.assertEqual(player.achievement_notification["expiresAtMs"], 3000)
        self.assertEqual(player.speaker_focus_controller.transition_started_at_ms, 1020)
        self.assertEqual(player.dialogue_camera_controller.transition_started_at_ms, 1040)


if __name__ == "__main__":
    unittest.main()
