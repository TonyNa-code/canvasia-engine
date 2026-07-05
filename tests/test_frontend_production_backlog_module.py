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
              routeOverview: {{
                metrics: {{ brokenRoutes: 1, unreachableScenes: 2, orphanScenes: 0 }},
                routeTestingPlan: {{
                  executionQueue: [
                    {{
                      severity: "blocker",
                      status: "broken",
                      title: "修复分支坏链",
                      actionLabel: "重新选择目标场景",
                      acceptanceCriteria: "确认状态变为可试玩。",
                      chapterName: "第1章",
                      sceneName: "分岔口",
                      routeLabel: "选项：留下",
                      targetLabel: "Missing",
                    }},
                    {{
                      severity: "warn",
                      status: "unreachable",
                      title: "接通结局入口",
                      actionLabel: "检查上游入口",
                      acceptanceCriteria: "玩家能自然打到该结局。",
                      chapterName: "第1章",
                      sceneName: "隐藏结局",
                      routeLabel: "结局路径",
                      targetLabel: "Hidden End",
                    }},
                    {{
                      severity: "test",
                      status: "ready",
                      title: "完整跑通结局",
                      chapterName: "第1章",
                      sceneName: "Good End",
                    }},
                  ],
                }},
              }},
              sceneBoard: {{
                issues: [
                  {{ severity: "warn", title: "缺少背景", detail: "补一张教室背景。", chapterName: "第1章", sceneName: "教室黄昏" }},
                  {{ severity: "tip", title: "演出变化偏少", detail: "加一次镜头推近。", chapterName: "第1章", sceneName: "天台" }},
                ],
              }},
              directorCueSheet: {{
                productionQueue: [
                  {{
                    severity: "blocker",
                    title: "分镜素材缺失",
                    actionLabel: "先修复素材或空场景",
                    detail: "音效门铃缺少真实文件。",
                    targetLabel: "第1章 / 教室黄昏",
                  }},
                  {{
                    severity: "warn",
                    title: "场景缺少背景",
                    actionLabel: "补齐基础演出",
                    detail: "走廊独白有正文但没有背景。",
                    targetLabel: "第1章 / 走廊独白",
                  }},
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
              assetRightsSheet: {{
                issues: [
                  {{ severity: "blocker", title: "已使用素材不可商用", detail: "字体授权仅限个人使用。", assetName: "不可商用字体" }},
                  {{ severity: "warn", title: "缺少来源或作者", detail: "BGM 没有登记来源。", assetName: "放课后钢琴" }},
                  {{ severity: "tip", title: "未使用素材缺授权记录", detail: "备用 CG 之后使用前需要补记录。", assetName: "备用 CG" }},
                ],
              }},
              audioCueSheet: {{
                productionQueue: [
                  {{
                    severity: "blocker",
                    title: "BGM 文件缺失",
                    actionLabel: "补齐或重新绑定素材",
                    detail: "缺少黄昏主题曲文件。",
                    targetLabel: "第1章 · 雨夜 · 黄昏主题",
                  }},
                  {{
                    severity: "tip",
                    title: "试听 BGM 覆盖段",
                    actionLabel: "从开头试听到切歌点",
                    detail: "确认切歌不突兀。",
                    targetLabel: "第1章 · 雨夜 · 放课后钢琴",
                  }},
                ],
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
              runtimeCapabilityMatrix: {{
                issues: [
                  {{ severity: "warn", title: "video_play：需要验收", detail: "原生 Runtime 视频依赖目标平台兜底。", blockType: "video_play", group: "视频", usedCount: 1, sceneNames: ["OP"] }},
                ],
              }},
              runtimePreloadBudget: {{
                releaseRiskLevel: "danger",
                warnings: [
                  {{
                    code: "critical_over_budget",
                    severity: "danger",
                    title: "首屏必备素材过重",
                    detail: "入口场景 OP 和 BGM 过大。",
                    actionHint: "先压缩 OP 或延后播放。",
                    assetName: "开场 OP",
                  }},
                  {{
                    code: "scene_hotspot",
                    severity: "warn",
                    title: "单场景加载热点偏重",
                    detail: "开场场景首屏素材过多。",
                    actionHint: "压缩背景和立绘。",
                    sceneName: "开场",
                  }},
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
        self.assertIn("addRouteExecutionTasks", payload["keys"])
        self.assertIn("addAudioProductionTasks", payload["keys"])
        self.assertIn("addDirectorCueTasks", payload["keys"])
        self.assertIn("addRuntimePreloadBudgetTasks", payload["keys"])
        self.assertEqual(payload["backlog"]["projectTitle"], "Backlog Demo")
        self.assertEqual(payload["backlog"]["summary"]["taskCount"], 24)
        self.assertEqual(payload["backlog"]["summary"]["blockerCount"], 8)
        self.assertEqual(payload["backlog"]["summary"]["warningCount"], 11)
        self.assertEqual(payload["backlog"]["summary"]["tipCount"], 5)
        self.assertGreaterEqual(payload["backlog"]["summary"]["areaCount"], 12)
        self.assertEqual(payload["digest"]["status"], "blocked")
        self.assertEqual(payload["backlog"]["tasks"][0]["severity"], "blocker")
        self.assertTrue(any(task["title"] == "修复分支坏链" for task in payload["backlog"]["tasks"]))
        self.assertTrue(any(task["title"] == "BGM 文件缺失" for task in payload["backlog"]["tasks"]))
        self.assertTrue(any(task["area"] == "director" and task["title"] == "分镜素材缺失" for task in payload["backlog"]["tasks"]))
        self.assertTrue(any(task["area"] == "loading" and task["title"] == "首屏必备素材过重" for task in payload["backlog"]["tasks"]))
        self.assertIn("生产待办队列", payload["markdown"])
        self.assertIn("修复分支坏链", payload["markdown"])
        self.assertIn("BGM 文件缺失", payload["markdown"])
        self.assertIn("语音文件缺失", payload["markdown"])
        self.assertIn("Runtime 覆盖", payload["markdown"])
        self.assertIn("导演分镜", payload["markdown"])
        self.assertIn("素材授权", payload["markdown"])
        self.assertIn("已使用素材不可商用", payload["markdown"])
        self.assertIn("首屏加载", payload["markdown"])
        self.assertIn("首屏必备素材过重", payload["markdown"])
        self.assertIn('"素材依赖"', payload["csv"])
        self.assertIn('"素材授权"', payload["csv"])
        self.assertIn('"首屏加载"', payload["csv"])
        self.assertEqual(payload["labels"], ["先修", "优先", "整理"])


if __name__ == "__main__":
    unittest.main()
