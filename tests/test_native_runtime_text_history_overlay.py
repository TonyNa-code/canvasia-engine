from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from native_runtime.runtime_text_history_overlay import handle_runtime_text_history_overlay_event


ROOT_DIR = Path(__file__).resolve().parents[1]


class FakePygame:
    KEYDOWN = 1
    TEXTINPUT = 2
    MOUSEWHEEL = 3
    MOUSEBUTTONDOWN = 4
    K_BACKSPACE = 10
    K_RETURN = 11
    K_KP_ENTER = 12
    K_UP = 13
    K_DOWN = 14
    K_PAGEUP = 15
    K_PAGEDOWN = 16
    K_SLASH = 17
    K_f = 18
    K_v = 19
    K_c = 20
    K_r = 21
    K_SPACE = 22


class FakeRuntime:
    def __init__(self) -> None:
        self.pygame = FakePygame()
        self.history_search_active = False
        self.history_search_query = ""
        self.history_speaker_filter = ""
        self.history_voiced_only = False
        self.history_scroll_index = 4
        self.status_message = ""
        self.overlay_hotspots = []
        self.moves: list[int] = []
        self.voice_replays = 0
        self.closed = 0
        self.cycled_speakers = 0
        self.cleared = 0

    def append_text_history_search(self, value: object) -> None:
        self.history_search_query += str(value or "")

    def set_text_history_search_active(self, active: bool) -> None:
        self.history_search_active = bool(active)

    def get_filtered_text_history_entries(self) -> list[tuple[int, dict]]:
        return [(2, {"text": "a"}), (4, {"text": "b"})]

    def move_text_history_selection(self, delta: int) -> None:
        self.moves.append(delta)

    def cycle_text_history_speaker(self) -> None:
        self.cycled_speakers += 1
        self.history_speaker_filter = "Alice"

    def clear_text_history_filters(self) -> None:
        self.cleared += 1
        self.history_search_query = ""
        self.history_speaker_filter = ""
        self.history_voiced_only = False

    def play_selected_history_voice(self) -> bool:
        self.voice_replays += 1
        return True

    def close_overlay(self) -> None:
        self.closed += 1


class NativeRuntimeTextHistoryOverlayTests(unittest.TestCase):
    def test_keyboard_search_filter_navigation_and_replay_routes_to_runtime(self) -> None:
        runtime = FakeRuntime()
        pygame = runtime.pygame

        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_SLASH))
        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.TEXTINPUT, text="秘密"))
        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_BACKSPACE))
        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_RETURN))
        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_UP))
        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_PAGEUP))
        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_f))
        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_v))
        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_r))
        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.KEYDOWN, key=pygame.K_c))

        self.assertFalse(runtime.history_search_active)
        self.assertEqual(runtime.history_search_query, "")
        self.assertEqual(runtime.moves, [-1, -5])
        self.assertEqual(runtime.cycled_speakers, 1)
        self.assertEqual(runtime.voice_replays, 1)
        self.assertEqual(runtime.cleared, 1)
        self.assertFalse(runtime.history_voiced_only)

    def test_mousewheel_and_close_keep_event_contract(self) -> None:
        runtime = FakeRuntime()
        pygame = runtime.pygame

        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.MOUSEWHEEL, y=1))
        handle_runtime_text_history_overlay_event(runtime, SimpleNamespace(type=pygame.MOUSEWHEEL, y=-1))

        class HitRect:
            @staticmethod
            def collidepoint(_position) -> bool:
                return True

        runtime.overlay_hotspots = [{"kind": "close", "rect": HitRect()}]
        handle_runtime_text_history_overlay_event(
            runtime,
            SimpleNamespace(type=pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10), clicks=1),
        )

        self.assertEqual(runtime.moves, [-1, 1])
        self.assertEqual(runtime.closed, 1)

    def test_runtime_player_delegates_render_and_events_to_overlay_module(self) -> None:
        source = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")

        self.assertIn("render_runtime_text_history_overlay(self, with_alpha)", source)
        self.assertIn("return handle_runtime_text_history_overlay_event(self, event)", source)


if __name__ == "__main__":
    unittest.main()
