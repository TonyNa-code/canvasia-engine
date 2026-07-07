from __future__ import annotations

import stat
import tempfile
import unittest
from pathlib import Path

from native_runtime_export_commands import NATIVE_RUNTIME_COMMAND_KEYS, write_native_runtime_command_files


def build_command_names() -> dict[str, str]:
    return {key: f"{key}.cmd" for key in NATIVE_RUNTIME_COMMAND_KEYS}


class NativeRuntimeExportCommandTests(unittest.TestCase):
    def test_write_native_runtime_command_files_creates_cross_platform_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            build_dir = Path(tmp_dir)
            paths = write_native_runtime_command_files(
                build_dir,
                command_names=build_command_names(),
                runtime_player_name="runtime_player.py",
                requirements_name="requirements-native-runtime.txt",
                build_requirements_name="requirements-native-runtime-build.txt",
            )

            self.assertEqual(set(paths), set(NATIVE_RUNTIME_COMMAND_KEYS))
            self.assertTrue(paths["mac_launcher"].is_file())
            self.assertTrue(paths["linux_launcher"].is_file())
            self.assertTrue(paths["windows_launcher"].is_file())
            self.assertIn("python3 runtime_player.py game_data.json", paths["mac_launcher"].read_text(encoding="utf-8"))
            self.assertIn("python3 runtime_player.py game_data.json", paths["linux_launcher"].read_text(encoding="utf-8"))
            self.assertIn("python runtime_player.py game_data.json", paths["windows_launcher"].read_text(encoding="utf-8"))
            self.assertIn(
                "python3 -m pip install -r requirements-native-runtime.txt -r requirements-native-runtime-build.txt",
                paths["mac_app_builder"].read_text(encoding="utf-8"),
            )
            self.assertTrue(paths["windows_launcher"].read_text(encoding="utf-8").splitlines()[0].startswith("@echo off"))
            self.assertTrue(paths["mac_launcher"].stat().st_mode & stat.S_IXUSR)
            self.assertTrue(paths["linux_app_builder"].stat().st_mode & stat.S_IXUSR)

    def test_write_native_runtime_command_files_requires_complete_name_map(self) -> None:
        names = build_command_names()
        names.pop("windows_app_builder")
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaisesRegex(ValueError, "windows_app_builder"):
                write_native_runtime_command_files(
                    Path(tmp_dir),
                    command_names=names,
                    runtime_player_name="runtime_player.py",
                    requirements_name="requirements-native-runtime.txt",
                    build_requirements_name="requirements-native-runtime-build.txt",
                )


if __name__ == "__main__":
    unittest.main()
