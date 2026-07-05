from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "release_control.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"


class FrontendReleaseControlModuleTests(unittest.TestCase):
    def test_final_publish_gate_is_visible_before_release_checklist(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("function buildFinalPublishGate", source)
        self.assertIn("function buildReleaseCreativeQualityContext", source)
        self.assertIn("creativeQuality: buildReleaseCreativeQualityContext()", source)
        self.assertIn("runtimeCapabilityMatrix: buildRuntimeCapabilityMatrix()", source)
        self.assertIn("routeTestingPlan: routeOverview?.routeTestingPlan ?? {}", source)
        self.assertIn("productionBacklogSummary: productionBacklog?.summary ?? null", source)
        self.assertIn("productionBacklogNextTask: productionBacklog?.nextTask ?? null", source)
        self.assertIn("function buildReleaseFixOrder(routeOverview)", source)
        self.assertIn("buildFinalPublishGate(releaseItems, releaseFixOrder, routeOverview)", source)
        self.assertIn("function serializeFinalPublishGate", source)
        self.assertIn("function renderFinalPublishGatePanel", source)
        self.assertIn("最终发表门禁", source)
        self.assertIn("finalPublishGate: serializeFinalPublishGate(finalPublishGate)", source)
        self.assertIn("## 最终发表门禁", source)
        self.assertIn("${renderFinalPublishGatePanel(routeOverview)}", source)
        self.assertLess(
            source.index("${renderFinalPublishGatePanel(routeOverview)}"),
            source.index("${renderReleaseChecklistPanel()}"),
        )

    def test_release_report_includes_route_testing_plan_context(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        report_start = source.index("function buildReleaseControlReportContent()")
        report_end = source.index("function exportReleaseControlReport()")
        report_body = source[report_start:report_end]

        self.assertIn("const routeTestingPlan = routeOverview.routeTestingPlan ?? {}", report_body)
        self.assertIn("const routeTestingSummary = routeTestingPlan.summary ?? {}", report_body)
        self.assertIn(
            "const routeTestingTables = routeTestingReportTools.buildRouteTestingReportTables(routeTestingPlan)",
            report_body,
        )
        self.assertIn("routeTestingTables.summaryTable", report_body)
        self.assertIn("routeTestingTables.decisionTable", report_body)
        self.assertIn("routeTestingTables.endingTable", report_body)
        self.assertIn("## 路线试玩手册", report_body)
        self.assertLess(report_body.index("const routeTestingPlan"), report_body.index("const routeTestingTables"))

    def test_release_fix_order_surfaces_route_issue_queue_in_ui_and_reports(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        payload_start = source.index("function buildReleaseControlReportPayload()")
        payload_end = source.index("function buildInspectionReportContent()")
        payload_body = source[payload_start:payload_end]
        report_start = source.index("function buildReleaseControlReportContent()")
        report_end = source.index("function exportReleaseControlReport()")
        report_body = source[report_start:report_end]

        self.assertIn("function serializeReleaseRouteIssue", source)
        self.assertIn("function renderReleaseRouteIssueQueue", source)
        self.assertIn("${renderReleaseRouteIssueQueue(step.routeIssueQueue)}", source)
        self.assertIn("routeIssueQueue: (step.routeIssueQueue ?? []).map(serializeReleaseRouteIssue)", payload_body)
        self.assertIn("const routeFixIssueTable = buildMarkdownTable", report_body)
        self.assertIn("### 具体路线阻塞", report_body)

    def test_release_report_includes_runtime_preload_budget_context(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        report_start = source.index("function buildReleaseControlReportContent()")
        report_end = source.index("function exportReleaseControlReport()")
        report_body = source[report_start:report_end]
        payload_start = source.index("function buildReleaseControlReportPayload()")
        payload_end = source.index("function buildInspectionReportContent()")
        payload_body = source[payload_start:payload_end]

        self.assertIn("const runtimePreloadBudgetReport = buildRuntimePreloadBudgetReport()", report_body)
        self.assertIn("const runtimePreloadBudgetDigest = runtimePreloadBudgetTools.getRuntimePreloadBudgetDigest", report_body)
        self.assertIn("const runtimePreloadBudgetRelease = serializeRuntimePreloadBudgetForRelease", report_body)
        self.assertIn("const productionBacklog = buildProductionBacklog(routeOverview)", report_body)
        self.assertIn("## Runtime 首屏加载预算", report_body)
        self.assertIn("runtimePreloadBudgetRelease.phaseRows", report_body)
        self.assertIn("runtimePreloadBudgetRelease.warningRows", report_body)
        self.assertIn("const releaseOverviewRows = buildReleaseControlOverviewRows", report_body)
        self.assertIn('buildMarkdownTable(["指标", "结果"], releaseOverviewRows)', report_body)
        self.assertIn("productionBacklogSummary: productionBacklog.summary", report_body)
        self.assertIn("runtimePreloadBudget: runtimePreloadBudgetRelease", payload_body)
        self.assertIn("productionBacklog: {", payload_body)
        self.assertIn("const runtimePreloadBudgetRelease = serializeRuntimePreloadBudgetForRelease", payload_body)

    def test_release_next_step_advice_is_module_backed(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        inspection_start = source.index("function buildInspectionReportContent()")
        inspection_end = source.index("function buildReleaseControlReportContent()")
        inspection_body = source[inspection_start:inspection_end]

        self.assertIn("releaseControlTools?.buildReleaseReportNextStep", source)
        self.assertIn("releaseControlTools?.formatReleaseReportNextStepActionHint", source)
        self.assertIn("releaseControlTools?.formatReleaseReportNextStepAdvice", source)
        self.assertIn("lines.push(`- ${formatReleaseReportNextStepAdvice(nextStep)}`);", inspection_body)
        self.assertNotIn("先清结构错误，再继续试玩和正式导出。", inspection_body)

    def test_release_control_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorReleaseControl;
            const action = {{
              label: "打开素材",
              action: "open-asset-from-issue",
              assetId: "asset_big_video",
              dataset: {{ "asset-filter-mode": "media_budget" }},
              privateValue: "should not leak",
            }};
            const releaseNextStep = tools.buildReleaseReportNextStep({{
              steps: [
                {{
                  title: "处理首屏加载压力",
                  description: "首屏偏重。",
                  statusLabel: "高风险 1 项",
                  actions: [{{ label: "查看首屏预算", action: "switch-screen", screen: "inspection" }}],
                }},
              ],
            }}, null);
            const milestoneNextStep = tools.buildReleaseReportNextStep({{ steps: [] }}, {{
              status: "gap",
              eyebrow: "当前阶段缺口",
              title: "第一版可试玩 Demo",
              description: "先把 Demo 跑起来。",
              primaryGap: {{
                label: "补试玩确认",
                missing: "缺一次完整试玩。",
                action: {{ label: "去试玩确认", action: "switch-screen", screen: "preview" }},
              }},
            }});
            const readyNextStep = tools.buildReleaseReportNextStep({{ steps: [] }}, {{ status: "ready" }});
            const result = {{
              labels: [
                tools.getReleaseSeverityLabel("blocker"),
                tools.getReleaseSeverityLabel("warn"),
                tools.getReleaseSeverityLabel("good"),
                tools.getReleaseSeverityLabel("custom"),
                tools.getReleaseStepToneLabel("danger"),
                tools.getReleaseStepToneLabel("warn"),
                tools.getReleaseStepToneLabel("good"),
                tools.getReleaseStepToneLabel("soft"),
              ],
              serializedAction: tools.serializeReleaseReportAction(action),
              nullAction: tools.serializeReleaseReportAction(null),
              blockerSummary: tools.buildReleaseChecklistSummary([
                {{ severity: "blocker" }},
                {{ severity: "warn" }},
                {{ severity: "good" }},
              ]),
              warnSummary: tools.buildReleaseChecklistSummary([
                {{ severity: "warn" }},
                {{ severity: "good" }},
                {{ severity: "good" }},
              ]),
              goodSummary: tools.buildReleaseChecklistSummary([
                {{ severity: "good" }},
                {{ severity: "good" }},
              ]),
              splitWarnings: tools.splitReleaseWarnings([
                {{ message: tools.MISSING_VOICE_WARNING_MESSAGE }},
                {{ message: "文本偏长。" }},
              ]),
              runtimePreloadCounts: [
                tools.getRuntimePreloadBudgetRiskCount({{ totals: {{ dangerCount: 1, warnCount: 2 }} }}),
                tools.getRuntimePreloadBudgetBlockerCount({{ warnings: [{{ severity: "danger" }}, {{ severity: "warn" }}] }}),
                tools.buildRuntimePreloadBudgetFixStep({{
                  releaseRiskLevel: "warn",
                  totals: {{ dangerCount: 0, warnCount: 1, totalLabel: "140 MB" }},
                  phases: {{
                    critical: {{ bytesLabel: "82 MB" }},
                    early: {{ bytesLabel: "140 MB" }},
                  }},
                  warnings: [
                    {{ severity: "warn", title: "开局过重", detail: "早期路线偏重。", actionHint: "把 OP 延后。" }},
                  ],
                }}).title,
              ],
              runtimePreloadRelease: tools.serializeRuntimePreloadBudgetForRelease({{
                releaseRiskLevel: "danger",
                totals: {{ dangerCount: 1, warnCount: 1, totalEntries: 3, totalBytes: 360 * 1024 * 1024, totalLabel: "360 MB" }},
                phases: {{
                  critical: {{ label: "首屏必备", count: 2, bytes: 180 * 1024 * 1024, bytesLabel: "180 MB", budgetLabel: "96 MB", missingFileCount: 1, overBudget: true }},
                  early: {{ label: "早期路线", count: 1, bytes: 180 * 1024 * 1024, bytesLabel: "180 MB", budgetLabel: "256 MB", missingFileCount: 0, overBudget: false }},
                }},
                phaseList: [
                  {{ label: "首屏必备", count: 2, bytesLabel: "180 MB", budgetLabel: "96 MB", missingFileCount: 1, overBudget: true }},
                ],
                warnings: [
                  {{ code: "critical_over_budget", severity: "danger", title: "首屏必备素材过重", detail: "首屏过重。", actionHint: "压入口素材。", assetId: "asset_op", assetName: "OP" }},
                  {{ code: "early_over_budget", severity: "warn", title: "早期路线偏重", detail: "早期偏重。", actionHint: "延后加载。", sceneId: "scene_1", sceneName: "开场" }},
                ],
                topEntries: [
                  {{ id: "asset_op", name: "OP", type: "video", typeLabel: "视频", phase: "critical", sizeBytes: 260 * 1024 * 1024, sizeLabel: "260 MB", fileExists: false, sceneId: "scene_1", sceneName: "开场", reason: "开场 / video_play" }},
                ],
              }}, {{ title: "首屏压力偏高", detail: "先处理入口压力。" }}),
              overviewRows: tools.buildReleaseControlOverviewRows({{
                errorCount: 2,
                warningCount: 3,
                urgentMissingAssetsCount: 4,
                unusedAssetCount: 5,
                mediaBudgetReport: {{ count: 6, totalLabel: "480 MB" }},
                runtimePreloadBudgetRelease: {{ summaryLine: "首屏压力偏高，首屏 180 MB / 早期 180 MB" }},
                routeMetrics: {{
                  entrySceneName: "开场",
                  branchingScenes: 2,
                  endingScenes: 3,
                  orphanScenes: 1,
                  reachableEndingScenes: 2,
                  reachableScenes: 8,
                  unreachableScenes: 1,
                  maxRouteDepth: 5,
                  brokenRoutes: 1,
                }},
                endingPaths: [
                  {{ isReachable: false, pathLabel: "坏线" }},
                  {{ isReachable: true, pathLabel: "开场 -> 真结局" }},
                ],
                routeTestingSummary: {{ decisionPointCount: 2, routeCaseCount: 4, endingTestCaseCount: 3 }},
                projectMilestonePlan: {{ nextMilestone: {{ title: "第一版可试玩 Demo" }}, overallScore: 72 }},
                projectMilestoneGapDigest: {{ eyebrow: "当前阶段缺口", title: "补齐试玩确认" }},
                productionBacklogSummary: {{ taskCount: 9, blockerCount: 2, warningCount: 4, tipCount: 3, readinessPercent: 48 }},
              }}),
              nextSteps: [
                releaseNextStep,
                milestoneNextStep,
                readyNextStep,
              ],
              nextStepAdvice: [
                tools.formatReleaseReportNextStepAdvice(releaseNextStep),
                tools.formatReleaseReportNextStepAdvice(milestoneNextStep),
                tools.formatReleaseReportNextStepAdvice(readyNextStep),
              ],
              desktopReady: [
                tools.isDesktopExportReady({{ target: "windows_nwjs", runtimeMode: "nwjs", missingAssets: 0 }}),
                tools.isDesktopExportReady({{ target: "windows_nwjs", runtimeMode: "fallback", missingAssets: 0 }}),
                tools.isDesktopExportReady({{ target: "web", runtimeMode: "nwjs", missingAssets: 0 }}),
                tools.isDesktopExportReady({{ target: "linux_nwjs", runtimeMode: "nwjs", missingAssets: 2 }}),
              ],
              blockedGate: tools.buildFinalPublishGate({{
                releaseChecklistItems: [
                  {{ severity: "blocker", title: "结构错误", description: "还有坏链", action: {{ label: "只看结构错误", action: "set-preview-issue-filter" }} }},
                  {{ severity: "warn", title: "语音覆盖", description: "还有待绑语音" }},
                  {{ severity: "good", title: "发布版本" }},
                ],
                releaseFixOrder: {{ steps: [{{ title: "先清结构错误", actions: [{{ label: "一键生成修复顺序", action: "generate-release-fix-order" }}] }}] }},
                regressionSummary: {{ failCount: 1, warnCount: 0 }},
                hasRegressionRun: true,
                exportResult: {{ targetLabel: "Windows 桌面包" }},
              }}),
              previewGate: tools.buildFinalPublishGate({{
                releaseChecklistItems: [
                  {{ severity: "warn", title: "语音覆盖", description: "还有待绑语音", action: {{ label: "只看待绑语音", action: "focus-script-missing-voice" }} }},
                  {{ severity: "good", title: "发布版本" }},
                ],
                hasRegressionRun: false,
                exportResult: {{ targetLabel: "网页包" }},
              }}),
              readyGate: tools.buildFinalPublishGate({{
                releaseChecklistItems: [
                  {{ severity: "good", title: "发布版本" }},
                  {{ severity: "good", title: "结构错误" }},
                ],
                regressionSummary: {{ failCount: 0, warnCount: 0 }},
                hasRegressionRun: true,
                exportResult: {{ targetLabel: "macOS 桌面包" }},
              }}),
              productionBlockedGate: tools.buildFinalPublishGate({{
                releaseChecklistItems: [
                  {{ severity: "good", title: "发布版本" }},
                  {{ severity: "good", title: "结构错误" }},
                ],
                regressionSummary: {{ failCount: 0, warnCount: 0 }},
                hasRegressionRun: true,
                exportResult: {{ targetLabel: "Linux 桌面包" }},
                productionBacklogSummary: {{
                  taskCount: 4,
                  blockerCount: 1,
                  warningCount: 2,
                  tipCount: 1,
                }},
                productionBacklogNextTask: {{
                  title: "补齐空白场景内容",
                  action: {{ label: "补演出卡", action: "switch-screen", screen: "story" }},
                }},
              }}),
              vnEssentialsSteps: tools.buildVnEssentialsReleaseSteps({{
                issues: [
                  {{ code: "bgm_scope_missing", area: "audio", severity: "warn", severityLabel: "基础缺口", title: "多首 BGM 缺少明确播放范围", detail: "两首曲子没有结束范围。", suggestion: "给关键曲目设置结束范围。" }},
                  {{ code: "dialog_box_readability", area: "textbox", severity: "soft", severityLabel: "体验打磨", title: "文本框可读性需要复看", detail: "正文对比度偏低。", suggestion: "提高文本框底色和文字对比度。" }},
                  {{ code: "background_coverage", area: "visual", severity: "warn", title: "背景覆盖不完整", detail: "已有创作品质检查覆盖，不应重复塞进基础项发布顺序。" }},
                ],
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
        self.assertEqual(
            payload["labels"],
            ["阻塞", "提醒", "通过", "custom", "先修", "优先", "确认", "收尾"],
        )
        self.assertEqual(payload["serializedAction"]["label"], "打开素材")
        self.assertEqual(payload["serializedAction"]["assetId"], "asset_big_video")
        self.assertEqual(payload["serializedAction"]["dataset"], {"asset-filter-mode": "media_budget"})
        self.assertNotIn("privateValue", payload["serializedAction"])
        self.assertIsNone(payload["nullAction"])
        self.assertEqual(payload["blockerSummary"]["badge"], "先补阻塞项")
        self.assertEqual(payload["blockerSummary"]["metrics"], [["阻塞项", "1 个"], ["提醒项", "1 个"], ["已就绪", "1 项"]])
        self.assertEqual(payload["warnSummary"]["badge"], "基本可发")
        self.assertEqual(payload["goodSummary"]["badge"], "可以交付")
        self.assertEqual(len(payload["splitWarnings"]["missingVoiceWarnings"]), 1)
        self.assertEqual(len(payload["splitWarnings"]["nonVoiceWarnings"]), 1)
        self.assertEqual(payload["runtimePreloadCounts"], [3, 1, "处理首屏加载压力"])
        self.assertEqual(payload["runtimePreloadRelease"]["summaryLine"], "首屏压力偏高，首屏 180 MB / 早期 180 MB")
        self.assertEqual(payload["runtimePreloadRelease"]["budgetLine"], "180 MB / 180 MB / 360 MB")
        self.assertEqual(payload["runtimePreloadRelease"]["warningCount"], 2)
        self.assertEqual(payload["runtimePreloadRelease"]["phaseRows"][0][5], "超过建议预算")
        self.assertEqual(payload["runtimePreloadRelease"]["warningRows"][0][0], "高风险")
        self.assertEqual(payload["runtimePreloadRelease"]["topEntries"][0]["assetId"], "asset_op")
        overview_rows = {row[0]: row[1] for row in payload["overviewRows"]}
        self.assertEqual(overview_rows["结构错误"], "2 项")
        self.assertEqual(overview_rows["首屏加载压力"], "首屏压力偏高，首屏 180 MB / 早期 180 MB")
        self.assertEqual(overview_rows["生产待办"], "9 项，先修 2 / 优先 4 / 润色 3，就绪度 48%")
        self.assertEqual(overview_rows["第一条结局路径"], "开场 -> 真结局")
        self.assertEqual(overview_rows["成品目标路线"], "第一版可试玩 Demo（72%）")
        self.assertEqual(payload["nextSteps"][0]["source"], "release_fix_order")
        self.assertEqual(payload["nextSteps"][0]["sourceLabel"], "发布修复顺序")
        self.assertEqual(payload["nextSteps"][0]["action"]["screen"], "inspection")
        self.assertIn("处理首屏加载压力", payload["nextStepAdvice"][0])
        self.assertEqual(payload["nextSteps"][1]["source"], "project_milestone_gap")
        self.assertEqual(payload["nextSteps"][1]["action"]["label"], "去试玩确认")
        self.assertIn("补试玩确认", payload["nextStepAdvice"][1])
        self.assertEqual(payload["nextSteps"][2]["tone"], "good")
        self.assertEqual(payload["nextStepAdvice"][2], "当前没有明显阻塞，可以直接做最终试玩和正式导出。")
        self.assertEqual(payload["desktopReady"], [True, False, False, False])
        self.assertEqual(payload["blockedGate"]["status"], "blocked")
        self.assertEqual(payload["blockedGate"]["badge"], "暂缓发布")
        self.assertEqual(payload["blockedGate"]["primaryAction"]["action"], "set-preview-issue-filter")
        self.assertEqual(payload["blockedGate"]["metrics"][0]["value"], "2 个")
        self.assertEqual(payload["blockedGate"]["checklist"][0]["label"], "结构错误")
        self.assertEqual(payload["previewGate"]["status"], "preview")
        self.assertEqual(payload["previewGate"]["primaryAction"]["action"], "run-preview-regression")
        self.assertEqual(payload["previewGate"]["metrics"][3]["value"], "网页包")
        self.assertEqual(payload["readyGate"]["status"], "ready")
        self.assertEqual(payload["readyGate"]["badge"], "可以公开发布")
        self.assertEqual(payload["readyGate"]["primaryAction"]["action"], "export-release-control-report")
        self.assertEqual(payload["readyGate"]["secondaryActions"][0]["dataset"], {"export-target": "web"})
        self.assertEqual(payload["productionBlockedGate"]["status"], "blocked")
        self.assertEqual(payload["productionBlockedGate"]["primaryAction"]["screen"], "story")
        self.assertEqual(payload["productionBlockedGate"]["metrics"][0]["value"], "1 个")
        self.assertEqual(payload["productionBlockedGate"]["metrics"][1]["value"], "2 个")
        self.assertEqual(payload["productionBlockedGate"]["metrics"][4]["label"], "生产待办")
        self.assertEqual(payload["productionBlockedGate"]["metrics"][4]["value"], "4 项")
        self.assertEqual(payload["productionBlockedGate"]["checklist"][0]["label"], "生产待办：补齐空白场景内容")
        self.assertIn("制作先修未完成", payload["productionBlockedGate"]["description"])
        self.assertEqual([step["title"] for step in payload["vnEssentialsSteps"]], ["多首 BGM 缺少明确播放范围", "文本框可读性需要复看"])
        self.assertEqual(payload["vnEssentialsSteps"][0]["tone"], "warn")
        self.assertEqual(payload["vnEssentialsSteps"][0]["actions"][0]["screen"], "story")
        self.assertEqual(payload["vnEssentialsSteps"][1]["actions"][0]["screen"], "project")

    def test_release_fix_order_prioritizes_blockers_before_polish(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorReleaseControl;
            const plan = tools.buildReleaseFixOrder({{
              resolution: {{ width: 1280, height: 720 }},
              releaseVersion: "1.2.0-preview",
              hasStoredReleaseVersion: false,
              errorCount: 2,
              warningIssues: [
                {{ message: tools.MISSING_VOICE_WARNING_MESSAGE }},
                {{ message: "台词偏长。" }},
              ],
              firstErrorAction: {{ action: "switch-screen", screen: "story", sceneId: "scene_1" }},
              firstVoiceAction: {{ action: "preview-story-location", sceneId: "scene_1", blockId: "line_1" }},
              firstWarningAction: {{ action: "preview-story-location", sceneId: "scene_2", blockId: "line_9" }},
              routeMetrics: {{ orphanScenes: 1, unreachableScenes: 2 }},
              urgentMissingAssetsCount: 3,
	              mediaBudgetReport: {{
	                count: 2,
	                blockerCount: 1,
	                totalLabel: "680 MB",
	                largest: {{ name: "opening.mp4", assetId: "video_op" }},
	              }},
	              runtimeCapabilityMatrix: {{
	                essentials: {{
	                  issues: [
	                    {{ code: "bgm_scope_missing", area: "audio", severity: "warn", severityLabel: "基础缺口", title: "多首 BGM 缺少明确播放范围", detail: "两首曲子没有结束范围。", suggestion: "给关键曲目设置结束范围。" }},
	                  ],
	                }},
	              }},
	              runtimePreloadBudget: {{
                releaseRiskLevel: "danger",
                totals: {{ dangerCount: 1, warnCount: 1, totalLabel: "360 MB" }},
                phases: {{
                  critical: {{ bytesLabel: "180 MB" }},
                  early: {{ bytesLabel: "360 MB" }},
                }},
                warnings: [
                  {{ severity: "danger", title: "首屏必备素材过重", detail: "首屏阶段已经达到 180 MB。", actionHint: "先压入口背景和 OP。" }},
                ],
                topEntries: [
                  {{ id: "op_video", name: "opening.mp4", sizeLabel: "260 MB", sceneName: "开场" }},
                ],
              }},
              unusedAssetCount: 4,
              exportResult: {{ target: "web", runtimeMode: "web", missingAssets: 0 }},
            }});
            const readyPlan = tools.buildReleaseFixOrder({{
              resolution: {{ width: 1920, height: 1080 }},
              releaseVersion: "1.2.0",
              hasStoredReleaseVersion: true,
              errorCount: 0,
              warningIssues: [],
              routeMetrics: {{ orphanScenes: 0, unreachableScenes: 0 }},
              urgentMissingAssetsCount: 0,
              mediaBudgetReport: {{ count: 0, blockerCount: 0 }},
              unusedAssetCount: 0,
              exportResult: {{ target: "macos_nwjs", runtimeMode: "nwjs", missingAssets: 0 }},
            }});
            process.stdout.write(JSON.stringify({{
              blockerPlan: plan,
              readyPlan,
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
        blocker_plan = payload["blockerPlan"]
        titles = [step["title"] for step in blocker_plan["steps"]]
        self.assertEqual(
            titles,
            [
                "先清结构错误",
	                "检查孤立场景和路线入口",
	                "补齐已引用缺口素材",
	                "多首 BGM 缺少明确播放范围",
	                "压缩超预算素材",
	                "处理首屏加载压力",
                "集中补待绑语音",
                "确认发布版本和分辨率",
                "顺手处理补充提醒",
                "清一轮闲置素材",
                "再导一版正式桌面包",
            ],
        )
        self.assertEqual(blocker_plan["blockerCount"], 1)
        self.assertEqual(blocker_plan["urgentCount"], 7)
        self.assertEqual(blocker_plan["steps"][0]["actions"][1]["label"], "打开第一条错误")
        self.assertEqual(blocker_plan["steps"][1]["statusLabel"], "还有 1 个孤立场景 / 2 个不可达场景")
        self.assertEqual(blocker_plan["steps"][3]["actions"][0]["screen"], "story")
        self.assertEqual(blocker_plan["steps"][4]["actions"][1]["assetId"], "video_op")
        self.assertEqual(blocker_plan["steps"][5]["actions"][1]["action"], "export-runtime-preload-budget-markdown")
        self.assertEqual(blocker_plan["steps"][7]["actions"][0]["action"], "save-release-version")

        ready_plan = payload["readyPlan"]
        self.assertEqual(len(ready_plan["steps"]), 1)
        self.assertEqual(ready_plan["steps"][0]["title"], "最后导出正式桌面包确认")
        self.assertEqual(ready_plan["steps"][0]["tone"], "good")
        self.assertEqual(ready_plan["blockerCount"], 0)
        self.assertEqual(ready_plan["urgentCount"], 0)

    def test_release_fix_order_surfaces_production_backlog_steps(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorReleaseControl;
            const baseContext = {{
              resolution: {{ width: 1920, height: 1080 }},
              releaseVersion: "1.2.0",
              hasStoredReleaseVersion: true,
              errorCount: 0,
              warningIssues: [],
              routeMetrics: {{ orphanScenes: 0, unreachableScenes: 0 }},
              urgentMissingAssetsCount: 0,
              mediaBudgetReport: {{ count: 0, blockerCount: 0 }},
              runtimePreloadBudget: {{ releaseRiskLevel: "ready" }},
              unusedAssetCount: 0,
              exportResult: {{ target: "macos_nwjs", runtimeMode: "nwjs", missingAssets: 0 }},
            }};
            const blockerPlan = tools.buildReleaseFixOrder({{
              ...baseContext,
              productionBacklogSummary: {{ taskCount: 4, blockerCount: 1, warningCount: 2, tipCount: 1 }},
              productionBacklogNextTask: {{
                title: "补齐空白场景内容",
                action: {{ label: "补演出卡", action: "switch-screen", screen: "story" }},
              }},
            }});
            const warnPlan = tools.buildReleaseFixOrder({{
              ...baseContext,
              productionBacklogSummary: {{ taskCount: 3, blockerCount: 0, warningCount: 2, tipCount: 1 }},
              productionBacklogNextTask: {{
                title: "确认 BGM 播放范围",
                action: {{ label: "调 BGM", action: "switch-screen", screen: "story" }},
              }},
            }});
            const softPlan = tools.buildReleaseFixOrder({{
              ...baseContext,
              productionBacklogSummary: {{ taskCount: 2, blockerCount: 0, warningCount: 0, tipCount: 2 }},
              productionBacklogNextTask: {{
                title: "复查过短场景节奏",
                action: {{ label: "补演出", action: "switch-screen", screen: "story" }},
              }},
            }});
            process.stdout.write(JSON.stringify({{
              blockerPlan,
              warnPlan,
              softPlan,
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
        blocker_step = payload["blockerPlan"]["steps"][0]
        warn_step = payload["warnPlan"]["steps"][0]
        soft_step = payload["softPlan"]["steps"][0]

        self.assertEqual(blocker_step["tone"], "danger")
        self.assertEqual(blocker_step["title"], "处理生产待办先修项")
        self.assertEqual(blocker_step["statusLabel"], "先修 1 / 优先 2 / 润色 1")
        self.assertEqual(blocker_step["actions"][0]["screen"], "story")
        self.assertEqual(blocker_step["actions"][1]["action"], "export-production-backlog-markdown")
        self.assertEqual(payload["blockerPlan"]["blockerCount"], 1)
        self.assertEqual(warn_step["tone"], "warn")
        self.assertEqual(warn_step["title"], "确认生产待办优先项")
        self.assertEqual(payload["warnPlan"]["urgentCount"], 1)
        self.assertEqual(soft_step["tone"], "soft")
        self.assertEqual(soft_step["title"], "收尾生产待办润色项")
        self.assertEqual(payload["softPlan"]["blockerCount"], 0)
        self.assertEqual(payload["softPlan"]["urgentCount"], 0)

    def test_release_fix_order_promotes_route_playtest_blockers(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorReleaseControl;
            const routeTestingPlan = {{
              decisionPoints: [
                {{
                  sceneId: "scene_branch",
                  chapterName: "第1章",
                  sceneName: "分岔口",
                  routeDepth: 1,
                  routeCases: [
                    {{
                      label: "选项：留下",
                      sourceSceneId: "scene_branch",
                      sourceSceneName: "分岔口",
                      targetSceneId: "scene_missing",
                      targetSceneName: "Missing",
                      status: "broken",
                      statusLabel: "坏链",
                    }},
                    {{
                      label: "选项：离开",
                      sourceSceneId: "scene_branch",
                      sourceSceneName: "分岔口",
                      targetSceneId: "scene_normal",
                      targetSceneName: "Normal",
                      status: "ready",
                      statusLabel: "可试玩",
                    }},
                  ],
                }},
              ],
              endingTestCases: [
                {{
                  sceneId: "scene_hidden_end",
                  chapterName: "第1章",
                  sceneName: "隐藏结局",
                  status: "unreachable",
                  statusLabel: "未接通",
                  testingHint: "先补上游入口。",
                }},
              ],
            }};
            const routeQueue = tools.buildRoutePlaytestFixQueue(routeTestingPlan);
            const routeStep = tools.buildRoutePlaytestFixStep(routeTestingPlan);
            const plan = tools.buildReleaseFixOrder({{
              resolution: {{ width: 1920, height: 1080 }},
              releaseVersion: "1.2.0",
              hasStoredReleaseVersion: true,
              errorCount: 0,
              warningIssues: [],
              routeTestingPlan,
              routeMetrics: {{ orphanScenes: 0, unreachableScenes: 0 }},
              urgentMissingAssetsCount: 0,
              mediaBudgetReport: {{ count: 0, blockerCount: 0 }},
              unusedAssetCount: 0,
              exportResult: {{ target: "windows_nwjs", runtimeMode: "nwjs", missingAssets: 0 }},
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              routeQueue,
              routeStep,
              plan,
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
        self.assertIn("buildRoutePlaytestFixQueue", payload["keys"])
        self.assertIn("buildRoutePlaytestFixStep", payload["keys"])
        self.assertEqual(len(payload["routeQueue"]), 2)
        self.assertEqual(payload["routeQueue"][0]["title"], "修复分支坏链")
        self.assertEqual(payload["routeQueue"][1]["title"], "接通结局入口")
        self.assertEqual(payload["routeStep"]["title"], "先修路线坏链")
        self.assertEqual(payload["routeStep"]["actions"][0]["action"], "preview-story-location")
        self.assertEqual(payload["routeStep"]["actions"][0]["sceneId"], "scene_branch")
        self.assertEqual(payload["plan"]["steps"][0]["title"], "先修路线坏链")
        self.assertEqual(payload["plan"]["steps"][0]["tone"], "danger")
        self.assertEqual(len(payload["plan"]["steps"][0]["routeIssueQueue"]), 2)
        self.assertEqual(payload["plan"]["steps"][0]["routeIssueQueue"][0]["sceneName"], "分岔口")
        self.assertEqual(payload["plan"]["blockerCount"], 1)

    def test_creative_quality_audit_adds_vn_baseline_polish_steps(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorReleaseControl;
            const auditSteps = tools.buildCreativeQualityAudit({{
              creativeQuality: {{
                storySceneCount: 4,
                dialogueCount: 8,
                narrationCount: 1,
                choiceCount: 0,
                characterCount: 2,
                charactersWithSpriteCount: 1,
                characterShowCount: 0,
                characterHideCount: 0,
                scenesWithBackground: 2,
                scenesWithMusic: 1,
                scenesWithEffects: 0,
                placeholderAssetCount: 2,
                placeholderScriptCount: 3,
              }},
            }});
            const plan = tools.buildReleaseFixOrder({{
              resolution: {{ width: 1920, height: 1080 }},
              releaseVersion: "1.2.0",
              hasStoredReleaseVersion: true,
              errorCount: 0,
              warningIssues: [],
              routeMetrics: {{ orphanScenes: 0, unreachableScenes: 0 }},
              urgentMissingAssetsCount: 0,
              mediaBudgetReport: {{ count: 0, blockerCount: 0 }},
              unusedAssetCount: 0,
              exportResult: {{ target: "windows_nwjs", runtimeMode: "nwjs", missingAssets: 0 }},
              creativeQuality: {{
                storySceneCount: 4,
                dialogueCount: 8,
                narrationCount: 1,
                choiceCount: 0,
                characterCount: 2,
                charactersWithSpriteCount: 1,
                characterShowCount: 0,
                characterHideCount: 0,
                scenesWithBackground: 2,
                scenesWithMusic: 1,
                scenesWithEffects: 0,
                placeholderAssetCount: 2,
                placeholderScriptCount: 3,
              }},
            }});
            process.stdout.write(JSON.stringify({{ auditSteps, plan }}));
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
        audit_steps = payload["auditSteps"]
        self.assertEqual(
            [step["title"] for step in audit_steps],
            [
                "替换 Demo 占位内容",
                "补齐角色兜底立绘",
                "补角色显示/隐藏演出",
                "补齐场景背景覆盖",
                "补关键场景 BGM 规划",
                "补一个玩家选择节点",
                "补基础演出点缀",
            ],
        )
        self.assertEqual(audit_steps[0]["tone"], "warn")
        self.assertEqual(audit_steps[0]["actions"][0]["screen"], "story")
        self.assertIn("占位素材 2 个", audit_steps[0]["statusLabel"])
        self.assertEqual(audit_steps[1]["actions"][0]["screen"], "characters")
        self.assertEqual(audit_steps[3]["actions"][0]["dataset"], {"route-filter": "missing_background"})
        self.assertEqual(audit_steps[4]["actions"][0]["dataset"], {"route-filter": "missing_music"})
        self.assertEqual(audit_steps[-1]["actions"][1]["screen"], "script")
        self.assertEqual(payload["plan"]["steps"][0]["title"], "替换 Demo 占位内容")
        self.assertEqual(payload["plan"]["steps"][-1]["title"], "最后导出正式桌面包确认")
        self.assertEqual(payload["plan"]["urgentCount"], 4)


if __name__ == "__main__":
    unittest.main()
