from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_history.js"


class FrontendProjectHistoryModuleTests(unittest.TestCase):
    def test_project_history_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectHistory;
            const history = {{
              totalSnapshots: "bad",
              currentIndex: "1",
              canUndo: 1,
              canRedo: 0,
              currentSnapshot: {{ index: "1", kind: "auto", label: "当前自动快照", createdAt: "2026-05-06T10:00:00Z" }},
              timelineSnapshots: [
                {{ index: "0", kind: "manual", label: "  开工前检查点  ", createdAt: "2026-05-06T09:00:00Z" }},
                {{ index: "1", kind: "auto", label: "当前自动快照", createdAt: "2026-05-06T10:00:00Z", isCurrent: true }},
                {{ index: "2", kind: "baseline", label: "首个基线", createdAt: "2026-05-05T08:00:00Z" }},
                {{ index: "3", kind: "broken", label: "", createdAt: "" }},
                null,
                "ignored",
              ],
            }};
            const safeHistory = tools.getSafeProjectHistory(history);
            const preview = tools.formatHistoryRestorePreview({{
              changedFileCount: "8",
              changedItems: [
                {{ kind: "created", label: "新场景" }},
                {{ kind: "removed", path: "assets/old.png" }},
                {{ kind: "updated", label: "角色资料" }},
                {{ kind: "created", label: "多余项" }},
              ],
            }}, {{ itemLimit: 3 }});
            const result = {{
              keys: Object.keys(tools).sort(),
              defaults: {{
                history: tools.getSafeProjectHistory(null),
                recovery: tools.getSafeProjectSessionRecovery(null),
              }},
              safeHistory,
              sessionRecovery: tools.getSafeProjectSessionRecovery({{
                noticeActive: 1,
                lastUnexpectedExitAt: "  2026-05-06T11:00:00Z  ",
                lastUnexpectedExitStartedAt: "2026-05-06T10:30:00Z",
                lastEndedReason: "crash",
                message: "  编辑器上次可能没有正常关闭  ",
              }}),
              labels: [
                tools.getHistoryKindLabel("manual"),
                tools.getHistoryKindLabel("broken"),
                tools.getHistoryKindTone("baseline"),
                tools.getHistoryFilterLabel("current"),
                tools.getHistoryFilterLabel("broken"),
                tools.getHistoryChangeKindLabel("removed"),
                tools.getHistoryChangeKindLabel("updated"),
              ],
              lookup: {{
                current: tools.getHistorySnapshotByIndex("1", history)?.label,
                missing: tools.getHistorySnapshotByIndex("bad", history),
                previous: tools.getPreviousHistorySnapshot(history)?.label,
              }},
              filters: {{
                all: tools.getFilteredHistorySnapshots(history).map((snapshot) => snapshot.index),
                manual: tools.getFilteredHistorySnapshots(history, {{ filterMode: "manual" }}).map((snapshot) => snapshot.index),
                auto: tools.getFilteredHistorySnapshots(history, {{ filterMode: "auto" }}).map((snapshot) => snapshot.index),
                current: tools.getFilteredHistorySnapshots(history, {{ filterMode: "current" }}).map((snapshot) => snapshot.index),
                queryLabel: tools.getFilteredHistorySnapshots(history, {{ searchQuery: "检查点" }}).map((snapshot) => snapshot.index),
                queryKind: tools.getFilteredHistorySnapshots(history, {{ searchQuery: "自动快照" }}).map((snapshot) => snapshot.index),
                queryDate: tools.getFilteredHistorySnapshots(history, {{
                  searchQuery: "2026/05/06",
                  formatDate: (value) => value?.startsWith("2026-05-06") ? "2026/05/06" : "",
                }}).map((snapshot) => snapshot.index),
              }},
              matching: [
                tools.doesHistorySnapshotMatchFilter(history.timelineSnapshots[0], "manual"),
                tools.doesHistorySnapshotMatchFilter(history.timelineSnapshots[0], "current"),
                tools.doesHistorySnapshotMatchSearch(history.timelineSnapshots[0], "开工前"),
                tools.doesHistorySnapshotMatchSearch(history.timelineSnapshots[0], "不存在"),
              ],
              preview,
              previewNoDiff: tools.formatHistoryRestorePreview({{ changedFileCount: 0 }}),
              previewFallback: tools.formatHistoryRestorePreview(null),
              promptKey: tools.buildProjectRecoveryPromptKey("project_a", {{
                lastUnexpectedExitStartedAt: "2026-05-06T10:30:00Z",
              }}),
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
        self.assertIn("getSafeProjectHistory", payload["keys"])
        self.assertIn("formatHistoryRestorePreview", payload["keys"])
        self.assertEqual(payload["defaults"]["history"]["totalSnapshots"], 0)
        self.assertFalse(payload["defaults"]["recovery"]["noticeActive"])
        self.assertEqual(payload["safeHistory"]["totalSnapshots"], 4)
        self.assertEqual(payload["safeHistory"]["currentIndex"], 1)
        self.assertTrue(payload["safeHistory"]["canUndo"])
        self.assertFalse(payload["safeHistory"]["canRedo"])
        self.assertEqual(payload["safeHistory"]["timelineSnapshots"][0]["label"], "开工前检查点")
        self.assertEqual(payload["safeHistory"]["timelineSnapshots"][3]["label"], "未命名快照")
        self.assertEqual(payload["safeHistory"]["timelineSnapshots"][3]["kind"], "auto")
        self.assertTrue(payload["sessionRecovery"]["noticeActive"])
        self.assertEqual(payload["sessionRecovery"]["message"], "编辑器上次可能没有正常关闭")
        self.assertEqual(
            payload["labels"],
            ["手动检查点", "自动快照", "soft", "只看当前版本", "全部版本", "移除", "改动"],
        )
        self.assertEqual(payload["lookup"], {"current": "当前自动快照", "missing": None, "previous": "开工前检查点"})
        self.assertEqual(payload["filters"]["all"], [0, 1, 2, 3])
        self.assertEqual(payload["filters"]["manual"], [0])
        self.assertEqual(payload["filters"]["auto"], [1, 3])
        self.assertEqual(payload["filters"]["current"], [1])
        self.assertEqual(payload["filters"]["queryLabel"], [0])
        self.assertEqual(payload["filters"]["queryKind"], [1, 3])
        self.assertEqual(payload["filters"]["queryDate"], [0, 1])
        self.assertEqual(payload["matching"], [True, False, True, False])
        self.assertIn("恢复后会影响 8 处内容。", payload["preview"])
        self.assertIn("- 新场景（新增）", payload["preview"])
        self.assertIn("- assets/old.png（移除）", payload["preview"])
        self.assertIn("- 角色资料（改动）", payload["preview"])
        self.assertIn("- 另外还有 1 处变化", payload["preview"])
        self.assertEqual(payload["previewNoDiff"], "当前版本和目标版本没有差异。")
        self.assertEqual(payload["previewFallback"], "恢复后会把项目回到你选中的那个时间点。")
        self.assertEqual(payload["promptKey"], "project_a:2026-05-06T10:30:00Z")


if __name__ == "__main__":
    unittest.main()
