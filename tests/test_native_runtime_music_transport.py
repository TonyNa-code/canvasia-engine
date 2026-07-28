from __future__ import annotations

import unittest

from native_runtime.runtime_music_transport import (
    NativeMusicTransportController,
    build_music_playback_key,
    get_music_initial_position,
    is_simple_music_loop,
    sanitize_music_transport,
)


class NativeRuntimeMusicTransportTests(unittest.TestCase):
    def test_transport_defaults_are_backward_compatible(self) -> None:
        self.assertEqual(
            sanitize_music_transport(),
            {
                "loop": True,
                "startTimeSeconds": 0.0,
                "loopStartSeconds": 0.0,
                "loopEndSeconds": 0.0,
                "restartMode": "continue",
            },
        )
        self.assertTrue(is_simple_music_loop({}))
        self.assertEqual(sanitize_music_transport({"loopStartSeconds": 9, "loopEndSeconds": 4})["loopEndSeconds"], 0)

    def test_controller_restarts_custom_loop_and_tracks_absolute_position(self) -> None:
        controller = NativeMusicTransportController()
        controller.configure(
            {
                "loop": True,
                "startTimeSeconds": 2,
                "loopStartSeconds": 8,
                "loopEndSeconds": 15,
            }
        )
        self.assertEqual(controller.get_pygame_loop_count(), 0)
        self.assertFalse(controller.simple_loop)
        self.assertEqual(controller.get_start_position(), 2)
        self.assertEqual(controller.get_absolute_position(3000), 5)
        self.assertEqual(controller.get_restart_position(13000, True), 8)

        restarted: list[float] = []
        controller.restart_segment(8, restarted.append)
        self.assertEqual(restarted, [8])
        self.assertEqual(controller.get_absolute_position(2500), 10.5)
        controller.reset()
        self.assertFalse(controller.simple_loop)

    def test_resume_and_same_track_policy_are_deterministic(self) -> None:
        transport = {"loop": True, "loopStartSeconds": 8, "loopEndSeconds": 15}
        self.assertEqual(get_music_initial_position(transport, 18), 8)
        self.assertEqual(
            build_music_playback_key("bgm", {"restartMode": "continue"}, "a"),
            build_music_playback_key("bgm", {"restartMode": "continue"}, "b"),
        )
        self.assertNotEqual(
            build_music_playback_key("bgm", {"restartMode": "restart"}, "a"),
            build_music_playback_key("bgm", {"restartMode": "restart"}, "b"),
        )


if __name__ == "__main__":
    unittest.main()
