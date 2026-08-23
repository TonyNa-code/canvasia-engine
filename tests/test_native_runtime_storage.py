from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from native_runtime import runtime_storage


class NativeRuntimeStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.home_dir = Path(self.temporary_directory.name) / "home"
        self.home_dir.mkdir(parents=True)
        self.home_patch = mock.patch.dict(os.environ, {"HOME": str(self.home_dir)})
        self.home_patch.start()
        runtime_storage.consume_runtime_storage_recovery_events()

    def tearDown(self) -> None:
        runtime_storage.consume_runtime_storage_recovery_events()
        self.home_patch.stop()
        self.temporary_directory.cleanup()

    def test_save_store_recovers_previous_valid_generation_from_backup(self) -> None:
        first_store = {
            "quickSave": {"sceneName": "第一章", "blockIndex": 3},
            "formalSlots": [None, {"sceneName": "旧存档"}],
        }
        second_store = {
            "quickSave": {"sceneName": "第二章", "blockIndex": 8},
            "formalSlots": [{"sceneName": "新存档"}, None],
        }

        save_path = runtime_storage.write_project_save_store("storage_safety", first_store)
        backup_path = runtime_storage.get_runtime_json_backup_path(save_path)
        self.assertEqual(json.loads(save_path.read_text(encoding="utf-8")), first_store)
        self.assertEqual(json.loads(backup_path.read_text(encoding="utf-8")), first_store)

        runtime_storage.write_project_save_store("storage_safety", second_store)
        self.assertEqual(json.loads(save_path.read_text(encoding="utf-8")), second_store)
        self.assertEqual(json.loads(backup_path.read_text(encoding="utf-8")), first_store)

        save_path.write_text('{"quickSave":', encoding="utf-8")
        recovered = runtime_storage.load_project_save_store("storage_safety", 2)

        self.assertEqual(recovered["quickSave"], first_store["quickSave"])
        self.assertEqual(
            recovered["formalSlots"],
            [None, {"sceneName": "旧存档", "protected": False}],
        )
        self.assertEqual(json.loads(save_path.read_text(encoding="utf-8")), first_store)
        events = runtime_storage.consume_runtime_storage_recovery_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["label"], "正式存档")
        self.assertEqual(events[0]["filename"], save_path.name)

    def test_failed_serialization_and_replace_leave_existing_save_untouched(self) -> None:
        initial_store = {"quickSave": {"sceneName": "安全点"}, "formalSlots": [None]}
        save_path = runtime_storage.write_project_save_store("atomic_failure", initial_store)
        backup_path = runtime_storage.get_runtime_json_backup_path(save_path)
        original_primary = save_path.read_text(encoding="utf-8")
        original_backup = backup_path.read_text(encoding="utf-8")

        with self.assertRaises(TypeError):
            runtime_storage.write_project_save_store(
                "atomic_failure",
                {"quickSave": {"unsupported": {"set-value"}}, "formalSlots": [None]},
            )

        replacement_store = {"quickSave": {"sceneName": "不应覆盖"}, "formalSlots": [None]}
        with mock.patch.object(runtime_storage.os, "replace", side_effect=OSError("simulated replace failure")):
            with self.assertRaises(OSError):
                runtime_storage.write_project_save_store("atomic_failure", replacement_store)

        self.assertEqual(save_path.read_text(encoding="utf-8"), original_primary)
        self.assertEqual(backup_path.read_text(encoding="utf-8"), original_backup)
        self.assertEqual(list(save_path.parent.glob(f".{save_path.name}.*.tmp")), [])

    def test_clearing_auto_resume_removes_primary_and_recovery_copy(self) -> None:
        snapshot = {
            "sceneId": "scene_start",
            "sceneName": "开场",
            "blockIndex": 2,
        }
        auto_resume_path = runtime_storage.write_project_auto_resume("clear_resume", snapshot)
        backup_path = runtime_storage.get_runtime_json_backup_path(auto_resume_path)
        self.assertTrue(auto_resume_path.is_file())
        self.assertTrue(backup_path.is_file())

        runtime_storage.clear_project_auto_resume("clear_resume")

        self.assertFalse(auto_resume_path.exists())
        self.assertFalse(backup_path.exists())
        self.assertIsNone(runtime_storage.load_project_auto_resume("clear_resume"))
        self.assertEqual(runtime_storage.consume_runtime_storage_recovery_events(), [])


if __name__ == "__main__":
    unittest.main()
