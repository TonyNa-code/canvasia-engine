from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_save_portability.js"
STORAGE_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_storage.js"


class FrontendRuntimeSavePortabilityModuleTests(unittest.TestCase):
    def run_node(self, body: str) -> dict:
        script = textwrap.dedent(
            f"""
            import * as portability from {json.dumps(MODULE_PATH.as_uri())};
            import * as storageTools from {json.dumps(STORAGE_MODULE_PATH.as_uri())};
            {body}
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_backup_validation_compaction_restore_and_transactional_rollback(self) -> None:
        payload = self.run_node(
            """
            function createStorage() {
              return {
                values: new Map(),
                failOnceKey: "",
                failed: false,
                getItem(key) {
                  return this.values.has(key) ? this.values.get(key) : null;
                },
                setItem(key, value) {
                  if (key === this.failOnceKey && !this.failed) {
                    this.failed = true;
                    throw new Error("quota");
                  }
                  this.values.set(key, String(value));
                },
                removeItem(key) {
                  this.values.delete(key);
                },
              };
            }

            const project = {
              projectId: "project_portability",
              title: "迁移测试 / Demo",
              releaseVersion: "1.2.0",
            };
            const keys = storageTools.buildRuntimeStorageKeys(project);
            const storage = createStorage();
            storageTools.writeRuntimeStorageJson(keys.playback, { textSpeed: "fast", bgmVolume: 60 }, { storage });
            storageTools.writeRuntimeStorageJson(keys.saveSlots, [
              { savedAt: "2026-08-24T10:00:00Z", session: { sceneId: "scene_a" }, thumbnailDataUrl: "data:image/png;base64,abc" },
            ], { storage });
            storageTools.writeRuntimeStorageJson(keys.achievements, { first_step: { unlockedAt: "2026-08-24T10:01:00Z" } }, { storage });

            const backup = portability.createRuntimeSaveBackup(project, keys, {
              storage,
              now: new Date("2026-08-24T12:34:56Z"),
            });
            const serialized = portability.serializeRuntimeSaveBackup(backup);
            const parsed = portability.parseRuntimeSaveBackupText(serialized, { project, storageKeys: keys });
            const filename = portability.getRuntimeSaveBackupFileName(project, backup.exportedAt);

            const tampered = JSON.parse(serialized);
            tampered.records.playback.value.textSpeed = "instant";
            const tamperedResult = portability.validateRuntimeSaveBackup(tampered, { project, storageKeys: keys });
            const foreignResult = portability.validateRuntimeSaveBackup(backup, {
              project: { ...project, projectId: "another_project", title: "另一个游戏" },
              storageKeys: storageTools.buildRuntimeStorageKeys({ title: "另一个游戏" }),
            });
            const badJson = portability.parseRuntimeSaveBackupText("{broken", { project, storageKeys: keys });

            storageTools.writeRuntimeStorageJson(keys.playback, { textSpeed: "slow" }, { storage });
            storageTools.writeRuntimeStorageJson(keys.quickSave, { session: { sceneId: "temporary" } }, { storage });
            const restored = portability.restoreRuntimeSaveBackup(backup, { project, storageKeys: keys, storage });
            const restoredPlayback = storageTools.readRuntimeStorageJson(keys.playback, null, { storage });
            const restoredQuickSave = storageTools.readRuntimeStorageJson(keys.quickSave, "missing", { storage });

            const compactStorage = createStorage();
            storageTools.writeRuntimeStorageJson(keys.saveSlots, [
              { session: { sceneId: "scene_large" }, thumbnailDataUrl: `data:image/png;base64,${"x".repeat(12000)}` },
            ], { storage: compactStorage });
            const compactBackup = portability.createRuntimeSaveBackup(project, keys, {
              storage: compactStorage,
              characterLimit: 6000,
              now: new Date("2026-08-24T13:00:00Z"),
            });

            const rollbackStorage = createStorage();
            storageTools.writeRuntimeStorageJson(keys.playback, { textSpeed: "slow", marker: "keep" }, { storage: rollbackStorage });
            storageTools.writeRuntimeStorageJson(keys.quickSave, { session: { sceneId: "keep_me" } }, { storage: rollbackStorage });
            const beforeRollbackPlayback = rollbackStorage.getItem(keys.playback);
            const beforeRollbackQuickSave = rollbackStorage.getItem(keys.quickSave);
            rollbackStorage.failOnceKey = keys.saveSlots;
            const rollbackResult = portability.restoreRuntimeSaveBackup(backup, {
              project,
              storageKeys: keys,
              storage: rollbackStorage,
            });

            process.stdout.write(JSON.stringify({
              exports: Object.keys(portability).sort(),
              format: backup.format,
              version: backup.formatVersion,
              exportedAt: backup.exportedAt,
              project: backup.project,
              recordNames: Object.keys(backup.records).sort(),
              parsed,
              filename,
              tamperedResult,
              foreignResult,
              badJson,
              restored,
              restoredPlayback,
              restoredQuickSave,
              compactRemoved: compactBackup.compaction.thumbnailCountRemoved,
              compactThumbnail: compactBackup.records.saveSlots.value[0].thumbnailDataUrl,
              compactValidation: portability.validateRuntimeSaveBackup(compactBackup, { project, storageKeys: keys }),
              rollbackResult,
              rollbackPlaybackPreserved: rollbackStorage.getItem(keys.playback) === beforeRollbackPlayback,
              rollbackQuickSavePreserved: rollbackStorage.getItem(keys.quickSave) === beforeRollbackQuickSave,
            }));
            """
        )

        self.assertIn("createRuntimeSaveBackup", payload["exports"])
        self.assertIn("restoreRuntimeSaveBackup", payload["exports"])
        self.assertIn("createRuntimeSavePortabilityController", payload["exports"])
        self.assertEqual(payload["format"], "canvasia-runtime-save-backup")
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["exportedAt"], "2026-08-24T12:34:56.000Z")
        self.assertEqual(payload["project"]["projectId"], "project_portability")
        self.assertIn("playback", payload["recordNames"])
        self.assertIn("persistentVariables", payload["recordNames"])
        self.assertTrue(payload["parsed"]["ok"])
        self.assertEqual(payload["parsed"]["summary"]["storedRecordCount"], 3)
        self.assertTrue(payload["filename"].endswith(".canvasia-save.json"))
        self.assertNotIn("/", payload["filename"])
        self.assertEqual(payload["tamperedResult"]["code"], "integrity_mismatch")
        self.assertEqual(payload["foreignResult"]["code"], "project_mismatch")
        self.assertEqual(payload["badJson"]["code"], "invalid_json")
        self.assertTrue(payload["restored"]["ok"])
        self.assertEqual(payload["restoredPlayback"]["textSpeed"], "fast")
        self.assertEqual(payload["restoredQuickSave"], "missing")
        self.assertEqual(payload["compactRemoved"], 1)
        self.assertEqual(payload["compactThumbnail"], "")
        self.assertTrue(payload["compactValidation"]["ok"])
        self.assertEqual(payload["rollbackResult"]["code"], "restore_failed")
        self.assertTrue(payload["rollbackPlaybackPreserved"])
        self.assertTrue(payload["rollbackQuickSavePreserved"])

    def test_controller_requires_validation_and_explicit_restore_confirmation(self) -> None:
        payload = self.run_node(
            """
            function createRef() {
              return {
                listeners: new Map(),
                hidden: false,
                disabled: false,
                dataset: {},
                textContent: "",
                value: "",
                clickCount: 0,
                addEventListener(name, callback) { this.listeners.set(name, callback); },
                removeEventListener(name) { this.listeners.delete(name); },
                click() { this.clickCount += 1; this.listeners.get("click")?.({ target: this }); },
              };
            }
            const project = { projectId: "controller_project", title: "Controller Demo", releaseVersion: "1.0.0" };
            const keys = storageTools.buildRuntimeStorageKeys(project);
            const storage = {
              values: new Map(),
              getItem(key) { return this.values.has(key) ? this.values.get(key) : null; },
              setItem(key, value) { this.values.set(key, String(value)); },
              removeItem(key) { this.values.delete(key); },
            };
            storageTools.writeRuntimeStorageJson(keys.quickSave, { session: { sceneId: "portable" } }, { storage });
            const backup = portability.createRuntimeSaveBackup(project, keys, {
              storage,
              now: new Date("2026-08-24T14:00:00Z"),
            });
            const refs = {
              root: createRef(),
              exportButton: createRef(),
              importButton: createRef(),
              restoreButton: createRef(),
              fileInput: createRef(),
              status: createRef(),
            };
            const anchors = [];
            const documentRef = {
              body: { appendChild(anchor) { anchors.push(anchor); } },
              createElement() {
                return {
                  href: "",
                  download: "",
                  hidden: false,
                  clicked: false,
                  click() { this.clicked = true; },
                  remove() {},
                };
              },
            };
            const revoked = [];
            const urlApi = {
              createObjectURL() { return "blob:canvasia-save"; },
              revokeObjectURL(url) { revoked.push(url); },
            };
            let beforeRestoreCount = 0;
            let restoredCount = 0;
            let failedCount = 0;
            const controller = portability.createRuntimeSavePortabilityController({
              project,
              storageKeys: keys,
              storage,
              refs,
              documentRef,
              urlApi,
              BlobCtor: Blob,
              setTimeout(callback) { callback(); return 1; },
              onBeforeRestore() { beforeRestoreCount += 1; },
              onRestored() { restoredCount += 1; },
              onRestoreFailed() { failedCount += 1; },
              now: new Date("2026-08-24T14:30:00Z"),
            });
            controller.attach();
            const initial = controller.getSnapshot();
            controller.exportCurrentSave();
            const afterExportStatus = refs.status.textContent;

            storageTools.writeRuntimeStorageJson(keys.quickSave, { session: { sceneId: "current" } }, { storage });
            const inputTarget = {
              files: [{ size: 2000, text: async () => portability.serializeRuntimeSaveBackup(backup) }],
              value: "selected",
            };
            const validated = await controller.handleBackupFileChange({ target: inputTarget });
            const beforeConfirm = controller.getSnapshot();
            const pendingStatus = refs.status.textContent;
            const restored = controller.restorePendingSave();
            const restoredQuickSave = storageTools.readRuntimeStorageJson(keys.quickSave, null, { storage });
            controller.detach();

            process.stdout.write(JSON.stringify({
              initial,
              afterExportStatus,
              anchor: anchors[0],
              revoked,
              validated,
              beforeConfirm,
              pendingStatus,
              restoreButtonHidden: refs.restoreButton.hidden,
              restored,
              restoredQuickSave,
              beforeRestoreCount,
              restoredCount,
              failedCount,
              inputCleared: inputTarget.value === "",
              detached: controller.getSnapshot().attached,
            }));
            """
        )

        self.assertTrue(payload["initial"]["attached"])
        self.assertFalse(payload["initial"]["pending"])
        self.assertIn("已导出", payload["afterExportStatus"])
        self.assertTrue(payload["anchor"]["clicked"])
        self.assertTrue(payload["anchor"]["download"].endswith(".canvasia-save.json"))
        self.assertEqual(payload["revoked"], ["blob:canvasia-save"])
        self.assertTrue(payload["validated"])
        self.assertTrue(payload["beforeConfirm"]["pending"])
        self.assertIn("再次确认", payload["pendingStatus"])
        self.assertTrue(payload["restored"])
        self.assertEqual(payload["restoredQuickSave"]["session"]["sceneId"], "portable")
        self.assertEqual(payload["beforeRestoreCount"], 1)
        self.assertEqual(payload["restoredCount"], 1)
        self.assertEqual(payload["failedCount"], 0)
        self.assertTrue(payload["inputCleared"])
        self.assertFalse(payload["detached"])


if __name__ == "__main__":
    unittest.main()
