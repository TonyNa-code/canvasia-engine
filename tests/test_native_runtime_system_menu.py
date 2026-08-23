from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from native_runtime.runtime_system_menu import get_system_menu_item_description


ROOT_DIR = Path(__file__).resolve().parents[1]


class NativeRuntimeSystemMenuTests(unittest.TestCase):
    def test_save_vault_description_is_player_facing_and_specific(self) -> None:
        runtime = SimpleNamespace(
            text_history=[],
            auto_resume_snapshot=None,
            persistent_variable_state={},
            variables=[],
            build_save_summary_line=lambda: "正式存档 0/12",
        )

        description = get_system_menu_item_description(runtime, "save-vault")

        self.assertIn("完整性校验", description)
        self.assertIn("恢复前", description)
        self.assertNotIn("TODO", description)

    def test_player_delegates_system_menu_and_registers_save_vault_overlay(self) -> None:
        source = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        vault_source = (ROOT_DIR / "native_runtime" / "runtime_save_vault.py").read_text(encoding="utf-8")

        self.assertIn('("save-vault", "数据保险箱")', source)
        self.assertIn("render_runtime_system_menu_overlay(self, SYSTEM_MENU_ITEMS)", source)
        self.assertIn("handle_runtime_system_menu_event(self, event, SYSTEM_MENU_ITEMS)", source)
        self.assertIn('runtime.overlay_mode = "save-vault"', vault_source)
        self.assertIn("render_runtime_save_vault_overlay(self)", source)
        self.assertIn("handle_runtime_save_vault_event(self, event)", source)


if __name__ == "__main__":
    unittest.main()
