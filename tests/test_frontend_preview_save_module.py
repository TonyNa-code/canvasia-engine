from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "preview_save.js"


class FrontendPreviewSaveModuleTests(unittest.TestCase):
    def test_preview_save_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorPreviewSave;
            const sceneNames = new Map([["scene_a", {{ name: "序章教室" }}]]);
            const snapshotSource = {{
              sceneId: "scene_a",
              blockIndex: "2",
              blockId: 42,
              blockType: "choice",
              block: {{ text: "继续调查", nested: {{ ok: true }} }},
              visualState: {{ backgroundId: "bg_1" }},
              variables: {{ affection: 3 }},
              choiceOptions: [
                {{ id: "choice_a", text: "追上去" }},
                null,
                () => "ignored",
              ],
              transitionTargetSceneId: 99,
              selectedOptionId: "choice_a",
              resolvedBranchId: 77,
            }};
            const sanitizedSnapshot = tools.sanitizeStoredPreviewSnapshot(snapshotSource, {{
              getSceneById: (sceneId) => sceneNames.get(sceneId),
              cloneVisualState: (value) => ({{ clonedVisual: value?.backgroundId ?? "" }}),
              cloneVariables: (value) => ({{ clonedVariables: value?.affection ?? 0 }}),
            }});
            const sanitizedSession = tools.sanitizeStoredPreviewSession({{
              startSceneId: null,
              position: 99,
              timeline: [snapshotSource, null, {{ sceneId: "missing_scene", completed: true }}],
            }}, {{
              fallbackSceneId: "scene_fallback",
              getSafeSceneId: (sceneId) => sceneId ? `safe:${{sceneId}}` : "safe:fallback",
              sanitizeSnapshot: (snapshot) => tools.sanitizeStoredPreviewSnapshot(snapshot, {{
                getSceneById: (sceneId) => sceneNames.get(sceneId),
              }}),
            }});
            const sanitizedSlot = tools.sanitizeStoredPreviewSaveSlot({{
              savedAt: "",
              session: {{
                startSceneId: "scene_a",
                position: -10,
                timeline: [snapshotSource],
              }},
              thumbnailDataUrl: 123,
            }}, {{
              nowIso: () => "2026-05-06T00:00:00.000Z",
              sanitizeSession: (session) => tools.sanitizeStoredPreviewSession(session, {{
                getSafeSceneId: (sceneId) => sceneId ?? "fallback",
              }}),
            }});
            const cloned = tools.deepClonePreviewData({{ nested: {{ value: 1 }} }});
            cloned.nested.value = 99;

            const result = {{
              keys: Object.keys(tools).sort(),
              constants: [tools.PREVIEW_SAVE_SHORTCUT_COUNT, tools.PREVIEW_SAVE_DIALOG_PAGE_SIZE],
              slotIndexes: [
                tools.getSafePreviewSaveSlotIndex("1", 50),
                tools.getSafePreviewSaveSlotIndex(50, 50),
                tools.getSafePreviewSaveSlotIndex("0", 50),
                tools.getSafePreviewSaveSlotIndex("51", 50),
                tools.getSafePreviewSaveSlotIndex("abc", 50),
              ],
              pageCount: tools.getPreviewSaveDialogPageCount(50, 6),
              safePages: [
                tools.getSafePreviewSaveDialogPage(-2, {{ slotCount: 50, pageSize: 6, currentPage: 3 }}),
                tools.getSafePreviewSaveDialogPage(999, {{ slotCount: 50, pageSize: 6, currentPage: 3 }}),
                tools.getSafePreviewSaveDialogPage("bad", {{ slotCount: 50, pageSize: 6, currentPage: 3 }}),
              ],
              modes: [
                tools.getSafePreviewSaveDialogMode("load"),
                tools.getSafePreviewSaveDialogMode("save"),
                tools.getSafePreviewSaveDialogMode("broken"),
              ],
              emptySlots: tools.createEmptyPreviewSaveSlots(4),
              sanitizedSnapshot,
              sanitizedSession,
              sanitizedSlot,
              cloneIsolation: cloned.nested.value,
              invalids: [
                tools.sanitizeStoredPreviewSnapshot(null),
                tools.sanitizeStoredPreviewSession({{ timeline: [] }}),
                tools.sanitizeStoredPreviewSaveSlot({{ session: {{ timeline: [] }} }}),
              ],
            }};
            process.stdout.write(JSON.stringify(result));
            """
        )
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("sanitizeStoredPreviewSession", payload["keys"])
        self.assertEqual(payload["constants"], [3, 6])
        self.assertEqual(payload["slotIndexes"], [0, 49, None, None, None])
        self.assertEqual(payload["pageCount"], 9)
        self.assertEqual(payload["safePages"], [0, 8, 3])
        self.assertEqual(payload["modes"], ["load", "save", "save"])
        self.assertEqual(payload["emptySlots"], [None, None, None, None])
        self.assertEqual(payload["sanitizedSnapshot"]["sceneName"], "序章教室")
        self.assertEqual(payload["sanitizedSnapshot"]["blockIndex"], 2)
        self.assertEqual(payload["sanitizedSnapshot"]["blockId"], "42")
        self.assertEqual(payload["sanitizedSnapshot"]["visualState"], {"clonedVisual": "bg_1"})
        self.assertEqual(payload["sanitizedSnapshot"]["variables"], {"clonedVariables": 3})
        self.assertEqual(len(payload["sanitizedSnapshot"]["choiceOptions"]), 1)
        self.assertEqual(payload["sanitizedSnapshot"]["transitionTargetSceneId"], "99")
        self.assertEqual(payload["sanitizedSnapshot"]["resolvedBranchId"], "77")
        self.assertEqual(payload["sanitizedSession"]["startSceneId"], "safe:scene_a")
        self.assertEqual(payload["sanitizedSession"]["position"], 1)
        self.assertEqual(len(payload["sanitizedSession"]["timeline"]), 2)
        self.assertEqual(payload["sanitizedSession"]["timeline"][1]["blockType"], "complete")
        self.assertEqual(payload["sanitizedSlot"]["savedAt"], "2026-05-06T00:00:00.000Z")
        self.assertEqual(payload["sanitizedSlot"]["session"]["position"], 0)
        self.assertEqual(payload["sanitizedSlot"]["thumbnailDataUrl"], "")
        self.assertEqual(payload["cloneIsolation"], 99)
        self.assertEqual(payload["invalids"], [None, None, None])


if __name__ == "__main__":
    unittest.main()
