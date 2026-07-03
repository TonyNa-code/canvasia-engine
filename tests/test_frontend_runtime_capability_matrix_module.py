from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "runtime_capability_matrix.js"


class FrontendRuntimeCapabilityMatrixModuleTests(unittest.TestCase):
    def test_runtime_capability_matrix_flags_partial_and_unknown_runtime_coverage(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorRuntimeCapabilityMatrix;
            const data = {{
              project: {{ title: "Runtime Demo" }},
              assetList: [
                {{ id: "bg_room", type: "background", name: "教室", fileExists: true }},
                {{ id: "scene_3d", type: "scene3d", name: "3D 教室", fileExists: true }},
                {{ id: "op_video", type: "video", name: "OP", fileExists: true }},
              ],
              chapters: [
                {{
                  chapterId: "chapter_1",
                  name: "第1章",
                  scenes: [
                    {{
                      id: "scene_start",
                      name: "开场",
                      blocks: [
                        {{ id: "bg", type: "background", assetId: "bg_room" }},
                        {{ id: "line", type: "dialogue", speakerId: "char_a", text: "你好。" }},
                        {{ id: "scene3d", type: "background", assetId: "scene_3d" }},
                        {{ id: "wait", type: "wait", durationSeconds: 1.2 }},
                        {{ id: "op", type: "video_play", assetId: "op_video" }},
                        {{ id: "future", type: "live2d_pose", characterId: "char_a" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const matrix = tools.buildRuntimeCapabilityMatrix(data);
            const digest = tools.getRuntimeCapabilityStatusDigest(matrix);
            const markdown = tools.buildRuntimeCapabilityMarkdown(matrix, {{
              projectTitle: "Runtime Demo",
              generatedAt: "2026-07-04 04:00:00",
            }});
            const csv = tools.buildRuntimeCapabilityCsv(matrix);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              matrix,
              digest,
              markdown,
              csv,
              labels: [
                tools.getRuntimeStatusLabel("full"),
                tools.getRuntimeStatusLabel("partial"),
                tools.getRuntimeStatusLabel("unknown"),
              ],
            }}));
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
        self.assertIn("buildRuntimeCapabilityMatrix", payload["keys"])
        self.assertIn("buildRuntimeAcceptanceChecklist", payload["keys"])
        self.assertIn("buildRuntimeCapabilityMarkdown", payload["keys"])
        self.assertIn("buildRuntimeCapabilityCsv", payload["keys"])
        summary = payload["matrix"]["summary"]
        self.assertEqual(summary["totalBlockCount"], 6)
        self.assertEqual(summary["usedTypeCount"], 5)
        self.assertEqual(summary["fullUsedTypeCount"], 2)
        self.assertEqual(summary["partialUsedTypeCount"], 2)
        self.assertEqual(summary["unknownUsedTypeCount"], 1)
        self.assertEqual(summary["scene3dBackgroundCount"], 1)
        self.assertEqual(summary["issueCount"], 3)
        acceptance_summary = payload["matrix"]["acceptance"]["summary"]
        self.assertGreaterEqual(acceptance_summary["itemCount"], 7)
        self.assertGreaterEqual(acceptance_summary["blockerCount"], 1)
        self.assertGreaterEqual(acceptance_summary["nativeItemCount"], 2)
        acceptance_titles = [item["title"] for item in payload["matrix"]["acceptance"]["items"]]
        self.assertTrue(any("视频播放" in title for title in acceptance_titles))
        self.assertTrue(any("3D 场景背景" in title for title in acceptance_titles))
        self.assertTrue(any("live2d_pose" in title for title in acceptance_titles))
        self.assertEqual(payload["digest"]["status"], "blocked")
        issue_titles = [issue["title"] for issue in payload["matrix"]["issues"]]
        self.assertTrue(any("live2d_pose" in title for title in issue_titles))
        self.assertTrue(any("video_play" in title for title in issue_titles))
        self.assertIn("# Runtime Demo Runtime 覆盖矩阵", payload["markdown"])
        self.assertIn("## Runtime 验收清单", payload["markdown"])
        self.assertIn("原生 Runtime", payload["markdown"])
        self.assertIn("3D 场景背景", payload["markdown"])
        self.assertIn('"live2d_pose"', payload["csv"])
        self.assertEqual(payload["labels"], ["完整支持", "需要验收", "未知卡片"])


if __name__ == "__main__":
    unittest.main()
