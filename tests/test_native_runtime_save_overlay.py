from __future__ import annotations

import unittest
from types import SimpleNamespace

from native_runtime.runtime_save_overlay import handle_runtime_save_dialog_event


class FakeRect:
    def __init__(self, hit: bool = True) -> None:
        self.hit = hit

    def collidepoint(self, _position) -> bool:
        return self.hit


class FakePygame:
    KEYDOWN = 1
    MOUSEBUTTONDOWN = 2
    K_LEFT = 10
    K_RIGHT = 11
    K_UP = 12
    K_DOWN = 13
    K_a = 14
    K_d = 15
    K_RETURN = 16
    K_SPACE = 17
    K_p = 18
    K_1 = 19
    K_2 = 20
    K_3 = 21
    K_4 = 22
    K_5 = 23
    K_6 = 24


class FakeRuntime:
    def __init__(self) -> None:
        self.pygame = FakePygame()
        self.overlay_focus_index = 1
        self.overlay_mode = "save"
        self.overlay_hotspots = []
        self.calls: list[tuple] = []

    def get_save_dialog_slot_count(self) -> int:
        return 6

    def normalize_overlay_focus(self) -> None:
        self.calls.append(("normalize",))

    def change_save_dialog_page(self, delta: int) -> None:
        self.calls.append(("page", delta))

    def activate_overlay_slot(self, index: int) -> None:
        self.calls.append(("slot", index))

    def toggle_visible_save_slot_protection(self, index: int) -> None:
        self.calls.append(("protect", index))

    def open_save_dialog(self, mode: str) -> None:
        self.calls.append(("open", mode))

    def close_overlay(self) -> None:
        self.calls.append(("close",))


class NativeRuntimeSaveOverlayTests(unittest.TestCase):
    def test_keyboard_protection_shortcut_targets_focused_slot(self) -> None:
        runtime = FakeRuntime()
        event = SimpleNamespace(type=runtime.pygame.KEYDOWN, key=runtime.pygame.K_p)

        self.assertTrue(handle_runtime_save_dialog_event(runtime, event))
        self.assertEqual(runtime.calls, [("protect", 1)])

    def test_mouse_protection_hotspot_wins_before_slot_card(self) -> None:
        runtime = FakeRuntime()
        runtime.overlay_hotspots = [
            {"kind": "slot-protection", "value": 3, "rect": FakeRect()},
            {"kind": "slot", "value": 3, "rect": FakeRect()},
        ]
        event = SimpleNamespace(type=runtime.pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 20))

        self.assertTrue(handle_runtime_save_dialog_event(runtime, event))
        self.assertEqual(runtime.calls, [("protect", 3)])

    def test_mouse_switch_uses_opposite_dialog_mode(self) -> None:
        runtime = FakeRuntime()
        runtime.overlay_hotspots = [{"kind": "switch", "rect": FakeRect()}]
        event = SimpleNamespace(type=runtime.pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 20))

        handle_runtime_save_dialog_event(runtime, event)

        self.assertEqual(runtime.calls, [("open", "load")])


if __name__ == "__main__":
    unittest.main()
