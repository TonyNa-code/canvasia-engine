from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "production_backlog.js"


class FrontendProductionBacklogModuleTests(unittest.TestCase):
    def test_production_backlog_merges_cross_module_tasks(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProductionBacklog;
            const backlog = tools.buildProductionBacklog({{
              projectTitle: "Backlog Demo",
              routeOverview: {{ metrics: {{ brokenRoutes: 1, unreachableScenes: 2, orphanScenes: 0 }} }},
              sceneBoard: {{
                issues: [
                  {{ severity: "warn", title: "缺少背景", detail: "补一张教室背景。", chapterName: "第1章", sceneName: "教室黄昏" }},
                  {{ severity: "tip", title: "演出变化偏少", detail: "加一次镜头推近。", chapterName: "第1章", sceneName: "天台" }},
                ],
              }},
              voiceSheet: {{
                issues: [
                  {{ severity: "blocker", title: "语音文件缺失", detail: "悠奈 001 没有真实文件。", chapterName: "第1章", sceneName: "教室黄昏", speakerName: "悠奈" }},
                ],
              }},
              choiceConsequenceSheet: {{
                issues: [
                  {{ severity: "warn", title: "疑似假选项", detail: "两个选项走向相同。", chapterName: "第1章", sceneName: "分岔口", optionText: "留下来" }},
                ],
              }},
              variableInfluenceSheet: {{ issues: [] }},
              assetDependencySheet: {{
                issues: [
                  {{ severity: "blocker", title: "素材文件缺失", detail: "背景图丢失。", assetName: "黄昏教室" }},
                  {{ severity: "tip", title: "未使用素材", detail: "可以清理。", assetName: "旧 CG" }},
                ],
              }},
              audioCueSheet: {{
                issues: [
                  {{ severity: "warn", title: "BGM 缺少淡出", detail: "切曲太硬。", chapterName: "第1章", sceneName: "雨夜" }},
                ],
              }},
              stageDirectionSheet: {{
                issues: [
                  {{ severity: "tip", title: "角色退场待补", detail: "老师持续留在舞台上。", sceneName: "放学后" }},
                ],
              }},
              presentationTimeline: {{
                issues: [
                  {{ severity: "warn", title: "静态文本过长", detail: "这一段太久没有画面变化。", sceneName: "独白" }},
                ],
              }},
              localizationCoverage: {{
                issues: [
                  {{ severity: "warn", title: "缺少日文翻译", detail: "这句还没翻译。", languageLabel: "日本語", sceneName: "教室黄昏" }},
                ],
              }},
            }});
            const digest = tools.getProductionBacklogStatusDigest(backlog);
            const markdown = tools.buildProductionBacklogMarkdown(backlog, {{
              projectTitle: "Backlog Demo",
              generatedAt: "2026-07-04 03:00:00",
            }});
            const csv = tools.buildProductionBacklogCsv(backlog);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              backlog,
              digest,
              markdown,
              csv,
              labels: [
                tools.getSeverityLabel("blocker"),
                tools.getSeverityLabel("warn"),
                tools.getSeverityLabel("tip"),
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
        self.assertIn("buildProductionBacklog", payload["keys"])
        self.assertIn("buildProductionBacklogMarkdown", payload["keys"])
        self.assertIn("buildProductionBacklogCsv", payload["keys"])
        self.assertEqual(payload["backlog"]["projectTitle"], "Backlog Demo")
        self.assertEqual(payload["backlog"]["summary"]["taskCount"], 12)
        self.assertEqual(payload["backlog"]["summary"]["blockerCount"], 3)
        self.assertEqual(payload["backlog"]["summary"]["warningCount"], 6)
        self.assertEqual(payload["backlog"]["summary"]["tipCount"], 3)
        self.assertGreaterEqual(payload["backlog"]["summary"]["areaCount"], 8)
        self.assertEqual(payload["digest"]["status"], "blocked")
        self.assertEqual(payload["backlog"]["tasks"][0]["severity"], "blocker")
        self.assertIn("生产待办队列", payload["markdown"])
        self.assertIn("语音文件缺失", payload["markdown"])
        self.assertIn('"素材依赖"', payload["csv"])
        self.assertEqual(payload["labels"], ["先修", "优先", "整理"])


if __name__ == "__main__":
    unittest.main()
