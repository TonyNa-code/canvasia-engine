from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from native_runtime import runtime_save_vault


ROOT_DIR = Path(__file__).resolve().parents[1]


def build_records(label: str = "current") -> dict:
    return {
        "saveStore": {
            "quickSave": {"sceneName": f"{label}-quick"},
            "formalSlots": [{"sceneName": f"{label}-formal"}, None, None],
        },
        "autoResume": {"sceneId": "opening", "sceneName": label, "blockIndex": 3},
        "archiveProgress": {
            "chapterReplayUnlocked": ["chapter-1"],
            "cgUnlocked": ["cg-1", "cg-2"],
            "readTextKeys": ["line-1"],
        },
        "playerProfile": {"sessionCount": 4, "totalPlayMs": 8000},
        "persistentVariables": {"formatVersion": 1, "values": {"route": label}},
        "runtimeSettings": {"themeMode": "dark", "textSpeed": "normal"},
    }


class NativeRuntimeSaveVaultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = {
            "projectId": "vault-project",
            "title": "保险箱测试",
            "releaseVersion": "1.2.0",
        }

    def test_bundle_round_trip_has_project_binding_integrity_and_summary(self) -> None:
        bundle = runtime_save_vault.build_save_vault_bundle(
            self.project,
            build_records(),
            exported_at="2026-08-24T10:30:00+08:00",
        )
        result = runtime_save_vault.validate_save_vault_bundle(
            json.loads(json.dumps(bundle, ensure_ascii=False)),
            expected_project_id="vault-project",
        )

        self.assertTrue(result["ok"])
        self.assertTrue(bundle["integrity"].startswith("sha256:"))
        self.assertEqual(result["summary"]["formalSaveCount"], 1)
        self.assertEqual(result["summary"]["formalSaveSlotCount"], 3)
        self.assertEqual(result["summary"]["unlockedCount"], 3)
        self.assertEqual(result["summary"]["persistentVariableCount"], 1)

    def test_bundle_without_project_id_uses_a_valid_stable_fallback(self) -> None:
        bundle = runtime_save_vault.build_save_vault_bundle({}, build_records())

        result = runtime_save_vault.validate_save_vault_bundle(
            bundle,
            expected_project_id="untitled_project",
        )

        self.assertTrue(result["ok"])
        self.assertEqual(bundle["project"]["projectId"], "untitled_project")

    def test_validation_rejects_tampering_and_other_projects(self) -> None:
        bundle = runtime_save_vault.build_save_vault_bundle(self.project, build_records())
        tampered = json.loads(json.dumps(bundle, ensure_ascii=False))
        tampered["records"]["saveStore"]["quickSave"]["sceneName"] = "被改写"

        integrity_result = runtime_save_vault.validate_save_vault_bundle(tampered)
        project_result = runtime_save_vault.validate_save_vault_bundle(
            bundle,
            expected_project_id="other-project",
        )

        self.assertEqual(integrity_result["code"], "integrity_mismatch")
        self.assertEqual(project_result["code"], "project_mismatch")

    def test_write_and_list_only_return_valid_project_vault_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path, bundle = runtime_save_vault.write_save_vault_bundle(
                self.project,
                build_records(),
                root_dir=root,
                exported_at="2026-08-24T10:30:00+08:00",
            )
            entries = runtime_save_vault.list_save_vault_entries("vault-project", root_dir=root)

            self.assertTrue(path.is_file())
            self.assertTrue(path.name.endswith(runtime_save_vault.SAVE_VAULT_EXTENSION))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), bundle)
            self.assertEqual(len(entries), 1)
            self.assertTrue(entries[0]["ok"])
            self.assertEqual(entries[0]["summary"]["projectId"], "vault-project")

    def test_sort_key_tolerates_a_backup_disappearing_during_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / f"moved{runtime_save_vault.SAVE_VAULT_EXTENSION}"

            modified_at, filename = runtime_save_vault._save_vault_sort_key(missing_path)

            self.assertEqual(modified_at, runtime_save_vault.SAVE_VAULT_MISSING_MTIME)
            self.assertEqual(filename, missing_path.name)

    def test_native_export_bundle_registers_vault_and_system_menu_modules(self) -> None:
        runner = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")

        self.assertIn('NATIVE_RUNTIME_SAVE_VAULT_NAME = "runtime_save_vault.py"', runner)
        self.assertIn('NATIVE_RUNTIME_SYSTEM_MENU_NAME = "runtime_system_menu.py"', runner)
        self.assertIn("NATIVE_RUNTIME_SAVE_VAULT_NAME,", runner)
        self.assertIn("NATIVE_RUNTIME_SYSTEM_MENU_NAME,", runner)

    def test_restore_applies_every_record_as_one_transaction(self) -> None:
        current = build_records("current")
        target = build_records("restored")
        state = json.loads(json.dumps(current, ensure_ascii=False))
        bundle = runtime_save_vault.build_save_vault_bundle(self.project, target)

        def write_record(name: str, value: object) -> None:
            state[name] = json.loads(json.dumps(value, ensure_ascii=False))

        result = runtime_save_vault.restore_save_vault_records(
            bundle,
            expected_project_id="vault-project",
            current_records=current,
            write_record=write_record,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(state, target)

    def test_failed_restore_rolls_back_all_applied_records(self) -> None:
        current = build_records("current")
        target = build_records("restored")
        state = json.loads(json.dumps(current, ensure_ascii=False))
        bundle = runtime_save_vault.build_save_vault_bundle(self.project, target)
        failure_injected = False
        write_counts: dict[str, int] = {}

        def write_record(name: str, value: object) -> None:
            nonlocal failure_injected
            write_counts[name] = write_counts.get(name, 0) + 1
            if name == "archiveProgress" and not failure_injected:
                failure_injected = True
                raise OSError("simulated disk failure")
            state[name] = json.loads(json.dumps(value, ensure_ascii=False))

        result = runtime_save_vault.restore_save_vault_records(
            bundle,
            expected_project_id="vault-project",
            current_records=current,
            write_record=write_record,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "restore_failed")
        self.assertTrue(result["details"]["rollbackComplete"])
        self.assertEqual(state, current)
        self.assertEqual(write_counts["saveStore"], 3)
        self.assertEqual(write_counts["autoResume"], 3)

    def test_restore_reports_when_a_rollback_write_also_fails(self) -> None:
        current = build_records("current")
        target = build_records("restored")
        bundle = runtime_save_vault.build_save_vault_bundle(self.project, target)

        def write_record(name: str, value: object) -> None:
            if name == "archiveProgress":
                raise OSError("persistent simulated failure")

        result = runtime_save_vault.restore_save_vault_records(
            bundle,
            expected_project_id="vault-project",
            current_records=current,
            write_record=write_record,
        )

        self.assertFalse(result["ok"])
        self.assertFalse(result["details"]["rollbackComplete"])
        self.assertIn("archiveProgress", result["details"]["rollbackErrors"][0])


if __name__ == "__main__":
    unittest.main()
