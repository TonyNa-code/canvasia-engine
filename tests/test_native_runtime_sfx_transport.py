from __future__ import annotations

import unittest

from native_runtime.runtime_sfx_transport import (
    NativeSfxTransportController,
    apply_sfx_block_to_channel_state,
    build_sfx_playback_key,
    sanitize_sfx_stop,
    sanitize_sfx_transport,
)


class FakeChannel:
    def __init__(self) -> None:
        self.busy = True
        self.volumes: list[float] = []
        self.stop_count = 0
        self.fadeouts: list[int] = []

    def get_busy(self) -> bool:
        return self.busy

    def set_volume(self, value: float) -> None:
        self.volumes.append(value)

    def stop(self) -> None:
        self.stop_count += 1
        self.busy = False

    def fadeout(self, duration_ms: int) -> None:
        self.fadeouts.append(duration_ms)
        self.busy = False


class FakeSound:
    def __init__(self) -> None:
        self.play_calls: list[dict] = []
        self.channels: list[FakeChannel] = []

    def play(self, loops: int = 0, fade_ms: int = 0) -> FakeChannel:
        self.play_calls.append({"loops": loops, "fade_ms": fade_ms})
        channel = FakeChannel()
        self.channels.append(channel)
        return channel


class NativeRuntimeSfxTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sounds = {name: FakeSound() for name in ("click", "rain", "wind")}
        self.master_volume = 0.5
        self.controller = NativeSfxTransportController(
            self.sounds.get,
            lambda: self.master_volume,
        )

    def test_defaults_state_reduction_and_keys_are_backward_compatible(self) -> None:
        self.assertEqual(
            sanitize_sfx_transport(),
            {
                "channelId": "effect",
                "loop": False,
                "restartMode": "restart",
                "volume": 100,
                "fadeInMs": 0,
                "replaceFadeOutMs": 0,
            },
        )
        self.assertEqual(sanitize_sfx_stop(), {"channelId": "all", "fadeOutMs": 600})
        state = apply_sfx_block_to_channel_state(
            {},
            {
                "id": "rain-a",
                "type": "sfx_play",
                "assetId": "rain",
                "channelId": "ambience",
                "loop": True,
            },
        )
        self.assertEqual(state["ambience"]["assetId"], "rain")
        self.assertEqual(
            apply_sfx_block_to_channel_state(state, {"type": "sfx_stop", "channelId": "ambience"}),
            {},
        )
        self.assertEqual(
            build_sfx_playback_key("rain", {"loop": True, "restartMode": "continue"}, "a"),
            build_sfx_playback_key("rain", {"loop": True, "restartMode": "continue"}, "b"),
        )
        self.assertNotEqual(
            build_sfx_playback_key("rain", {"loop": True, "restartMode": "restart"}, "a"),
            build_sfx_playback_key("rain", {"loop": True, "restartMode": "restart"}, "b"),
        )

    def test_controller_overlaps_one_shots_and_reuses_or_replaces_loops(self) -> None:
        self.assertTrue(self.controller.play({"assetId": "click", "volume": 80}, cue_id="click-a"))
        self.assertTrue(self.controller.play({"assetId": "click", "volume": 80}, cue_id="click-b"))
        self.assertEqual(len(self.controller.one_shots), 2)
        self.assertEqual(self.sounds["click"].play_calls, [{"loops": 0, "fade_ms": 0}] * 2)
        self.assertEqual(self.sounds["click"].channels[0].volumes[-1], 0.4)

        rain = {
            "assetId": "rain",
            "channelId": "ambience",
            "loop": True,
            "restartMode": "continue",
            "volume": 60,
            "fadeInMs": 300,
            "replaceFadeOutMs": 450,
        }
        self.assertTrue(self.controller.play(rain, cue_id="rain-a"))
        rain_channel = self.sounds["rain"].channels[0]
        self.assertTrue(self.controller.play(rain, cue_id="rain-b"))
        self.assertEqual(len(self.sounds["rain"].play_calls), 1)
        self.assertEqual(self.sounds["rain"].play_calls[0], {"loops": -1, "fade_ms": 300})

        wind = {
            "assetId": "wind",
            "channelId": "ambience",
            "loop": True,
            "restartMode": "continue",
            "volume": 40,
            "replaceFadeOutMs": 700,
        }
        self.assertTrue(self.controller.play(wind, cue_id="wind-a"))
        self.assertEqual(rain_channel.fadeouts, [700])
        self.assertEqual(self.controller.persistent_channels["ambience"].asset_id, "wind")

        self.master_volume = 1
        self.controller.update_volumes()
        self.assertEqual(self.sounds["wind"].channels[0].volumes[-1], 0.4)
        self.controller.stop({"channelId": "effect", "fadeOutMs": 250})
        self.assertEqual(len(self.controller.one_shots), 0)
        self.assertEqual(self.sounds["click"].channels[0].fadeouts, [250])
        self.assertIn("ambience", self.controller.persistent_channels)

    def test_persistent_channels_serialize_restore_and_stop(self) -> None:
        block = {
            "assetId": "rain",
            "channelId": "ambience",
            "loop": True,
            "restartMode": "continue",
            "volume": 55,
        }
        self.assertTrue(self.controller.play(block, cue_id="rain-save"))
        snapshot = self.controller.serialize_persistent_channels()
        self.assertEqual(snapshot["ambience"]["assetId"], "rain")

        restored_sounds = {"rain": FakeSound()}
        restored = NativeSfxTransportController(restored_sounds.get)
        self.assertEqual(restored.restore_persistent_channels(snapshot)["ambience"]["assetId"], "rain")
        self.assertEqual(restored_sounds["rain"].play_calls, [{"loops": -1, "fade_ms": 0}])
        restored.reset()
        self.assertEqual(restored.persistent_channels, {})
        self.assertEqual(restored_sounds["rain"].channels[0].stop_count, 1)


if __name__ == "__main__":
    unittest.main()
