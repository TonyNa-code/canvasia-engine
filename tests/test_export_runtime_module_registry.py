from __future__ import annotations

import unittest

from export_runtime_module_registry import (
    EXPORT_RUNTIME_MODULE_SPECS,
    build_export_runtime_module_manifest,
    get_export_runtime_module_files,
)


class ExportRuntimeModuleRegistryTests(unittest.TestCase):
    def test_registry_has_unique_keys_and_cross_runtime_player_modules(self) -> None:
        suffixes = [suffix for suffix, _file_name in EXPORT_RUNTIME_MODULE_SPECS]
        files = list(get_export_runtime_module_files())

        self.assertEqual(len(suffixes), len(set(suffixes)))
        self.assertEqual(len(files), len(set(files)))
        self.assertIn("runtime_text_history.js", files)
        self.assertIn("runtime_save_slots.js", files)
        self.assertIn("runtime_asset_pipeline.js", files)
        self.assertIn("runtime_playback_lifecycle.js", files)

    def test_manifest_builder_shapes_web_and_desktop_paths(self) -> None:
        web = build_export_runtime_module_manifest("playerRuntime")
        desktop = build_export_runtime_module_manifest("appRuntime", "app")

        self.assertEqual(web["playerRuntimeTextHistory"], "runtime_text_history.js")
        self.assertEqual(web["playerRuntimeSaveSlots"], "runtime_save_slots.js")
        self.assertEqual(web["playerRuntimeAssetPipeline"], "runtime_asset_pipeline.js")
        self.assertEqual(web["playerRuntimePlaybackLifecycle"], "runtime_playback_lifecycle.js")
        self.assertEqual(desktop["appRuntimeTextHistory"], "app/runtime_text_history.js")
        self.assertEqual(desktop["appRuntimeSaveSlots"], "app/runtime_save_slots.js")
        self.assertEqual(desktop["appRuntimeAssetPipeline"], "app/runtime_asset_pipeline.js")
        self.assertEqual(desktop["appRuntimePlaybackLifecycle"], "app/runtime_playback_lifecycle.js")
        self.assertEqual(set(web.values()), set(get_export_runtime_module_files()))
        self.assertEqual(
            {value.removeprefix("app/") for value in desktop.values()},
            set(get_export_runtime_module_files()),
        )

    def test_manifest_builder_rejects_unsafe_prefixes(self) -> None:
        with self.assertRaises(ValueError):
            build_export_runtime_module_manifest("player-runtime")
        with self.assertRaises(ValueError):
            build_export_runtime_module_manifest("appRuntime", "../outside")
        with self.assertRaises(ValueError):
            build_export_runtime_module_manifest("appRuntime", "app/../outside")


if __name__ == "__main__":
    unittest.main()
