from __future__ import annotations

import unittest
from pathlib import Path

from native_runtime.runtime_save_slots import (
    can_mutate_formal_save_slot,
    is_formal_save_slot_protected,
    normalize_formal_save_slots,
    toggle_formal_save_slot_protection,
    with_formal_save_slot_protection,
)


ROOT_DIR = Path(__file__).resolve().parents[1]


class NativeRuntimeSaveSlotsTests(unittest.TestCase):
    def test_old_and_malformed_slots_normalize_safely(self) -> None:
        old_slot = {"sceneName": "序章"}
        protected_slot = {"sceneName": "屋顶", "protected": True}

        slots = normalize_formal_save_slots([old_slot, protected_slot, "broken"], 5)

        self.assertEqual(len(slots), 5)
        self.assertFalse(slots[0]["protected"])
        self.assertTrue(slots[1]["protected"])
        self.assertIsNone(slots[2])
        self.assertIsNone(slots[4])
        self.assertNotIn("protected", old_slot)

    def test_protection_copy_does_not_mutate_snapshot(self) -> None:
        snapshot = {"sceneName": "选择之前", "protected": False}

        protected = toggle_formal_save_slot_protection(snapshot)
        unprotected = with_formal_save_slot_protection(protected, False)

        self.assertFalse(snapshot["protected"])
        self.assertTrue(is_formal_save_slot_protected(protected))
        self.assertFalse(can_mutate_formal_save_slot(protected))
        self.assertFalse(is_formal_save_slot_protected(unprotected))
        self.assertTrue(can_mutate_formal_save_slot(unprotected))
        self.assertIsNone(toggle_formal_save_slot_protection(None))

    def test_native_runtime_wires_protection_into_render_input_and_storage(self) -> None:
        player = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        overlay = (ROOT_DIR / "native_runtime" / "runtime_save_overlay.py").read_text(encoding="utf-8")
        view = (ROOT_DIR / "native_runtime" / "runtime_player_view.py").read_text(encoding="utf-8")
        storage = (ROOT_DIR / "native_runtime" / "runtime_storage.py").read_text(encoding="utf-8")
        exporter = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")

        self.assertIn("runtime_save_slots", player)
        self.assertIn("render_runtime_save_dialog_overlay(self)", player)
        self.assertIn("handle_runtime_save_dialog_event(self, event)", player)
        self.assertIn("slot-protection", overlay)
        self.assertIn("pygame.K_p", overlay)
        self.assertIn("can_mutate_formal_save_slot(previous_snapshot)", player)
        self.assertIn('"protected": bool(snapshot.get("protected") is True)', view)
        self.assertIn("normalize_formal_save_slots", storage)
        self.assertIn('NATIVE_RUNTIME_SAVE_SLOTS_NAME = "runtime_save_slots.py"', exporter)
        self.assertIn("NATIVE_RUNTIME_SAVE_SLOTS_NAME,", exporter)


if __name__ == "__main__":
    unittest.main()
