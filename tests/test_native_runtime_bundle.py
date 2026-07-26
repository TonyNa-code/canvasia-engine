from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from native_runtime_bundle import build_native_runtime_required_module_files


class NativeRuntimeBundleTests(unittest.TestCase):
    def test_registry_builds_stable_source_and_name_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            registry = build_native_runtime_required_module_files(
                root,
                ("runtime_player.py", "runtime_credits.py"),
            )

        self.assertEqual(
            registry,
            (
                (root / "runtime_player.py", "runtime_player.py"),
                (root / "runtime_credits.py", "runtime_credits.py"),
            ),
        )

    def test_registry_rejects_duplicates_and_nested_paths(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_native_runtime_required_module_files(Path("native"), ("runtime_player.py", "runtime_player.py"))
        with self.assertRaisesRegex(ValueError, "Invalid"):
            build_native_runtime_required_module_files(Path("native"), ("nested/runtime_player.py",))
        with self.assertRaisesRegex(ValueError, "Invalid"):
            build_native_runtime_required_module_files(Path("native"), (r"nested\runtime_player.py",))
        with self.assertRaisesRegex(ValueError, "Invalid"):
            build_native_runtime_required_module_files(Path("native"), ("README.md",))


if __name__ == "__main__":
    unittest.main()
