from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "runtime_preload_budget.js"


class FrontendRuntimePreloadBudgetModuleTests(unittest.TestCase):
    def test_runtime_preload_budget_report_flags_first_screen_pressure(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorRuntimePreloadBudget;
            const mb = 1024 * 1024;
            const data = {{
              project: {{
                title: "心跳时差",
                entrySceneId: "scene_opening",
                chapterOrder: ["chapter_01"],
                runtimeSettings: {{ performanceProfile: "mobile_low" }},
              }},
              assetList: [
                {{ id: "bg_start", type: "background", name: "教室清晨", fileExists: true, fileSizeBytes: 24 * mb, path: "bg/start.png" }},
                {{ id: "hero_smile", type: "sprite", name: "女主微笑", fileExists: true, fileSizeBytes: 12 * mb, path: "sprites/hero.png" }},
                {{ id: "bgm_theme", type: "bgm", name: "主旋律 WAV", fileExists: true, fileSizeBytes: 42 * mb, path: "audio/theme.wav" }},
                {{ id: "voice_001", type: "voice", name: "第一句语音", fileExists: false, fileSizeBytes: 0, path: "voice/001.ogg" }},
                {{ id: "op_video", type: "video", name: "开场 OP", fileExists: true, fileSizeBytes: 260 * mb, path: "video/op.mp4" }},
                {{ id: "favorite_ui", type: "ui", name: "标题 UI", favorite: true, fileExists: true, size: "4 MB" }},
              ],
              characters: {{
                characters: [
                  {{
                    id: "hero",
                    name: "女主",
                    defaultSpriteId: "hero_smile",
                    expressions: [{{ id: "smile", name: "微笑", spriteAssetId: "hero_smile" }}],
                  }},
                ],
              }},
              chapters: [
                {{
                  chapterId: "chapter_01",
                  name: "第一章",
                  sceneOrder: ["scene_opening", "scene_after"],
                  scenes: [
                    {{
                      id: "scene_opening",
                      name: "开场",
                      blocks: [
                        {{ id: "b1", type: "background", assetId: "bg_start" }},
                        {{ id: "b2", type: "character_show", characterId: "hero", expressionId: "smile" }},
                        {{ id: "b3", type: "music_play", assetId: "bgm_theme" }},
                        {{ id: "b4", type: "dialogue", speakerId: "hero", expressionId: "smile", text: "早上好。", voiceAssetId: "voice_001" }},
                        {{ id: "b5", type: "video_play", assetId: "op_video" }},
                      ],
                    }},
                    {{
                      id: "scene_after",
                      name: "放学后",
                      blocks: [
                        {{ id: "b6", type: "dialogue", speakerId: "hero", expressionId: "smile", text: "回家吧。" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const report = tools.buildRuntimePreloadBudgetReport(data, {{
              criticalBudgetBytes: 96 * mb,
              earlyBudgetBytes: 128 * mb,
              totalPreloadBudgetBytes: 256 * mb,
            }});
            const digest = tools.getRuntimePreloadBudgetDigest(report);
            const markdown = tools.buildRuntimePreloadBudgetMarkdown(report, {{
              projectTitle: "心跳时差",
              generatedAt: "2026-07-05",
            }});
            const csv = tools.buildRuntimePreloadBudgetCsv(report);
            console.log(JSON.stringify({{
              releaseRiskLevel: report.releaseRiskLevel,
              performanceProfile: report.performanceProfile,
              profileAdvice: report.profileAdvice,
              performanceBudgetLabel: report.budgets.performanceProfileLabel,
              warningCodes: report.warnings.map((warning) => warning.code),
              criticalBytes: report.phases.critical.bytes,
              criticalCount: report.phases.critical.count,
              libraryCount: report.phases.library.count,
              topIds: report.topEntries.slice(0, 3).map((entry) => entry.id),
              firstScene: report.scenes[0],
              digest,
              markdownHasSections: [
                markdown.includes("# 心跳时差 Runtime 首屏加载预算"),
                markdown.includes("低配 / 移动端"),
                markdown.includes("高画质 PC"),
                markdown.includes("## 性能档位建议"),
                markdown.includes("## 阶段预算"),
                markdown.includes("开场 OP"),
              ],
              csvHasRows: [
                csv.startsWith("\\uFEFF"),
                csv.includes("开场 OP"),
                csv.includes("首屏必备"),
              ],
              helperValues: [
                tools.getPreloadPhase(0, 12, "scene_opening", "scene_opening"),
                tools.getPreloadPhase(0, 13, "scene_opening", "scene_opening"),
                tools.getPreloadPhase(3, 0, "later", "scene_opening"),
                tools.getRuntimePreloadPerformanceProfile(data),
                tools.getSafePerformanceProfileKey("bad-profile"),
                tools.getRecommendedRuntimePreloadProfile(report.entries),
                tools.buildRuntimePreloadProfileMetrics(report.entries).videoEntryCount,
                tools.buildRuntimePreloadProfileAdvice(report.entries, "mobile_low").status,
                tools.formatBytes(1536),
                tools.normalizeAssetSizeBytes({{ size: "1.5 MB" }}),
              ],
            }}));
            """
        )
        result = subprocess.run(
            ["node", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(payload["releaseRiskLevel"], "danger")
        self.assertEqual(payload["performanceProfile"]["key"], "mobile_low")
        self.assertEqual(payload["profileAdvice"]["status"], "needs_optimization")
        self.assertEqual(payload["profileAdvice"]["recommendedProfile"], "high_quality_pc")
        self.assertEqual(payload["profileAdvice"]["recommendedProfileLabel"], "高画质 PC")
        self.assertEqual(payload["performanceBudgetLabel"], "低配 / 移动端")
        self.assertIn("critical_over_budget", payload["warningCodes"])
        self.assertIn("critical_missing_assets", payload["warningCodes"])
        self.assertIn("single_asset_over_budget", payload["warningCodes"])
        self.assertGreater(payload["criticalBytes"], 300 * 1024 * 1024)
        self.assertEqual(payload["criticalCount"], 5)
        self.assertEqual(payload["libraryCount"], 1)
        self.assertIn("op_video", payload["topIds"])
        self.assertEqual(payload["firstScene"]["sceneName"], "开场")
        self.assertTrue(payload["firstScene"]["overHotspotBudget"])
        self.assertEqual(payload["digest"]["level"], "danger")
        self.assertEqual(payload["digest"]["title"], "首屏压力偏高")
        self.assertTrue(all(payload["markdownHasSections"]))
        self.assertTrue(all(payload["csvHasRows"]))
        self.assertEqual(
            payload["helperValues"],
            ["critical", "early", "deferred", "mobile_low", "standard", "high_quality_pc", 1, "needs_optimization", "1.5 KB", 1572864],
        )


if __name__ == "__main__":
    unittest.main()
