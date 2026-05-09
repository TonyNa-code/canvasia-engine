from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_milestones.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"
STYLE_PATH = ROOT_DIR / "prototype_editor" / "styles.css"


class FrontendProjectMilestonesModuleTests(unittest.TestCase):
    def run_module_script(self, script_body: str) -> dict:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.TonyNaProjectMilestones;
            if (context.window.TonyNaEditorProjectMilestones !== tools) {{
              throw new Error("Project milestone module alias was not attached.");
            }}
            {script_body}
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
        return json.loads(completed.stdout)

    def test_project_milestones_prioritize_first_playable_gaps(self) -> None:
        payload = self.run_module_script(
            """
            const plan = tools.buildProjectMilestonePlan({
              totalChapters: 0,
              totalScenes: 0,
              scenesWithContent: 0,
              scenesWithBackground: 0,
              scenesWithMusic: 0,
              scenesWithEffects: 0,
              totalDialogueCount: 0,
              voicedDialogueCount: 0,
              readyAssetCount: 0,
              totalAssetCount: 0,
              validationErrorCount: 1,
              validationWarningCount: 3,
              brokenRoutes: 0,
              orphanScenes: 0,
              hasStarterKit: false,
              hasExport: false,
              regressionPass: false,
            });
            process.stdout.write(JSON.stringify({
              nextTitle: plan.nextMilestone.title,
              firstAction: plan.nextMilestone.actions[0],
              firstBlocker: plan.nextMilestone.blockers[0].id,
              milestoneCount: plan.milestones.length,
              overallScore: plan.overallScore,
            }));
            """
        )

        self.assertEqual(payload["nextTitle"], "第一版可试玩 Demo")
        self.assertEqual(payload["firstBlocker"], "structure")
        self.assertEqual(payload["firstAction"]["action"], "create-first-chapter")
        self.assertEqual(payload["milestoneCount"], 3)
        self.assertLess(payload["overallScore"], 50)

    def test_project_milestones_move_to_release_candidate_after_polish(self) -> None:
        payload = self.run_module_script(
            """
            const plan = tools.buildProjectMilestonePlan({
              totalChapters: 3,
              totalScenes: 5,
              scenesWithContent: 5,
              scenesWithBackground: 5,
              scenesWithMusic: 4,
              scenesWithEffects: 2,
              totalDialogueCount: 20,
              voicedDialogueCount: 14,
              readyAssetCount: 18,
              totalAssetCount: 20,
              validationErrorCount: 0,
              validationWarningCount: 2,
              brokenRoutes: 0,
              orphanScenes: 0,
              hasStarterKit: true,
              hasExport: false,
              regressionPass: false,
            });
            const release = plan.milestones.find((milestone) => milestone.id === "release_candidate");
            const exportAction = release.actions.find((action) => action.action === "export-build");
            process.stdout.write(JSON.stringify({
              nextTitle: plan.nextMilestone.title,
              completedCount: plan.completedCount,
              releaseDone: release.done,
              releaseBlockers: release.blockers.map((check) => check.id),
              releaseActions: release.actions.map((action) => action.action),
              exportDataset: exportAction.dataset,
            }));
            """
        )

        self.assertEqual(payload["nextTitle"], "发布候选版")
        self.assertEqual(payload["completedCount"], 2)
        self.assertFalse(payload["releaseDone"])
        self.assertEqual(payload["releaseBlockers"], ["regression", "exported"])
        self.assertEqual(payload["releaseActions"], ["run-preview-regression", "export-build"])
        self.assertEqual(payload["exportDataset"], {"export-target": "web"})

    def test_project_milestone_gap_digest_uses_current_phase_before_release(self) -> None:
        payload = self.run_module_script(
            """
            const earlyPlan = tools.buildProjectMilestonePlan({
              totalChapters: 0,
              totalScenes: 0,
              scenesWithContent: 0,
              scenesWithBackground: 0,
              scenesWithMusic: 0,
              scenesWithEffects: 0,
              totalDialogueCount: 0,
              voicedDialogueCount: 0,
              readyAssetCount: 0,
              totalAssetCount: 0,
              validationErrorCount: 1,
              validationWarningCount: 0,
              brokenRoutes: 0,
              orphanScenes: 0,
              hasStarterKit: false,
              hasExport: false,
              regressionPass: false,
            });
            const releasePlan = tools.buildProjectMilestonePlan({
              totalChapters: 3,
              totalScenes: 5,
              scenesWithContent: 5,
              scenesWithBackground: 5,
              scenesWithMusic: 4,
              scenesWithEffects: 2,
              totalDialogueCount: 20,
              voicedDialogueCount: 14,
              readyAssetCount: 18,
              totalAssetCount: 20,
              validationErrorCount: 0,
              validationWarningCount: 2,
              brokenRoutes: 0,
              orphanScenes: 0,
              hasStarterKit: true,
              hasExport: false,
              regressionPass: false,
            });
            const readyPlan = tools.buildProjectMilestonePlan({
              totalChapters: 3,
              totalScenes: 6,
              scenesWithContent: 6,
              scenesWithBackground: 6,
              scenesWithMusic: 5,
              scenesWithEffects: 3,
              totalDialogueCount: 30,
              voicedDialogueCount: 22,
              readyAssetCount: 29,
              totalAssetCount: 30,
              validationErrorCount: 0,
              validationWarningCount: 0,
              brokenRoutes: 0,
              orphanScenes: 0,
              hasStarterKit: true,
              hasExport: true,
              regressionPass: true,
            });
            process.stdout.write(JSON.stringify({
              early: tools.buildProjectMilestoneGapDigest(earlyPlan),
              release: tools.buildProjectMilestoneGapDigest(releasePlan),
              ready: tools.buildProjectMilestoneGapDigest(readyPlan),
            }));
            """
        )

        self.assertEqual(payload["early"]["eyebrow"], "当前阶段缺口")
        self.assertEqual(payload["early"]["gapMetricLabel"], "阶段缺口")
        self.assertEqual(payload["early"]["gapMetricHint"], "先清掉这一阶段")
        self.assertIn("第一版可试玩 Demo还差", payload["early"]["title"])
        self.assertEqual(payload["early"]["nextMilestoneTitle"], "第一版可试玩 Demo")
        self.assertEqual(payload["early"]["topGaps"][0]["id"], "structure")
        self.assertEqual(payload["early"]["nextAction"]["action"], "create-first-chapter")

        self.assertEqual(payload["release"]["eyebrow"], "发布候选差距")
        self.assertEqual(payload["release"]["gapMetricLabel"], "候选缺口")
        self.assertEqual(payload["release"]["status"], "close")
        self.assertEqual(payload["release"]["title"], "发布候选版还差 2 项")
        self.assertEqual([gap["id"] for gap in payload["release"]["topGaps"]], ["regression", "exported"])

        self.assertEqual(payload["ready"]["status"], "ready")
        self.assertEqual(payload["ready"]["title"], "发布候选核心条件已达标")
        self.assertEqual(payload["ready"]["topGaps"], [])

    def test_project_milestone_action_brief_guides_the_next_click(self) -> None:
        payload = self.run_module_script(
            """
            const earlyPlan = tools.buildProjectMilestonePlan({
              totalChapters: 0,
              totalScenes: 0,
              scenesWithContent: 0,
              scenesWithBackground: 0,
              scenesWithMusic: 0,
              scenesWithEffects: 0,
              totalDialogueCount: 0,
              voicedDialogueCount: 0,
              readyAssetCount: 0,
              totalAssetCount: 0,
              validationErrorCount: 1,
              validationWarningCount: 0,
              brokenRoutes: 0,
              orphanScenes: 0,
              hasStarterKit: false,
              hasExport: false,
              regressionPass: false,
            });
            const readyPlan = tools.buildProjectMilestonePlan({
              totalChapters: 3,
              totalScenes: 6,
              scenesWithContent: 6,
              scenesWithBackground: 6,
              scenesWithMusic: 5,
              scenesWithEffects: 3,
              totalDialogueCount: 30,
              voicedDialogueCount: 22,
              readyAssetCount: 29,
              totalAssetCount: 30,
              validationErrorCount: 0,
              validationWarningCount: 0,
              brokenRoutes: 0,
              orphanScenes: 0,
              hasStarterKit: true,
              hasExport: true,
              regressionPass: true,
            });
            process.stdout.write(JSON.stringify({
              early: tools.buildProjectMilestoneActionBrief(earlyPlan),
              ready: tools.buildProjectMilestoneActionBrief(readyPlan),
            }));
            """
        )

        self.assertEqual(payload["early"]["badge"], "优先推进")
        self.assertIn("先做：先创建第一章和第一场", payload["early"]["title"])
        self.assertEqual(payload["early"]["primaryAction"]["action"], "create-first-chapter")
        self.assertEqual(payload["early"]["metrics"][0]["label"], "总进度")
        self.assertEqual(payload["early"]["checklist"][0]["label"], "章节和场景骨架")
        self.assertEqual(payload["ready"]["tone"], "good")
        self.assertEqual(payload["ready"]["badge"], "准备验收")
        self.assertEqual(payload["ready"]["primaryAction"]["action"], "switch-screen")
        self.assertEqual(payload["ready"]["primaryAction"]["screen"], "preview")
        self.assertEqual(payload["ready"]["secondaryActions"][0]["action"], "export-build")
        self.assertEqual(payload["ready"]["secondaryActions"][0]["label"], "重新导出网页包")
        self.assertEqual(payload["ready"]["secondaryActions"][0]["dataset"], {"export-target": "web"})
        self.assertEqual(payload["ready"]["secondaryActions"][1]["action"], "switch-screen")
        self.assertEqual(payload["ready"]["secondaryActions"][1]["screen"], "inspection")
        self.assertEqual([item["label"] for item in payload["ready"]["checklist"]], ["人工长流程试玩", "整理发布附件", "撰写 Release notes"])

    def test_project_milestones_can_reach_all_done(self) -> None:
        payload = self.run_module_script(
            """
            const plan = tools.buildProjectMilestonePlan({
              totalChapters: 3,
              totalScenes: 6,
              scenesWithContent: 6,
              scenesWithBackground: 6,
              scenesWithMusic: 5,
              scenesWithEffects: 3,
              totalDialogueCount: 30,
              voicedDialogueCount: 22,
              readyAssetCount: 29,
              totalAssetCount: 30,
              validationErrorCount: 0,
              validationWarningCount: 0,
              brokenRoutes: 0,
              orphanScenes: 0,
              hasStarterKit: true,
              hasExport: true,
              regressionPass: true,
            });
            process.stdout.write(JSON.stringify({
              completedCount: plan.completedCount,
              totalCount: plan.totalCount,
              overallScore: plan.overallScore,
              headline: plan.headline,
            }));
            """
        )

        self.assertEqual(payload["completedCount"], payload["totalCount"])
        self.assertEqual(payload["overallScore"], 100)
        self.assertIn("三阶段目标都已达标", payload["headline"])

    def test_project_milestone_gap_digest_summarizes_release_candidate_gaps(self) -> None:
        payload = self.run_module_script(
            """
            const plan = tools.buildProjectMilestonePlan({
              totalChapters: 2,
              totalScenes: 4,
              scenesWithContent: 4,
              scenesWithBackground: 4,
              scenesWithMusic: 3,
              scenesWithEffects: 2,
              totalDialogueCount: 12,
              voicedDialogueCount: 8,
              readyAssetCount: 8,
              totalAssetCount: 10,
              validationErrorCount: 0,
              validationWarningCount: 1,
              brokenRoutes: 0,
              orphanScenes: 1,
              hasStarterKit: true,
              hasExport: false,
              regressionPass: false,
            });
            const digest = tools.buildProjectMilestoneGapDigest(plan);
            process.stdout.write(JSON.stringify({
              status: digest.status,
              title: digest.title,
              releaseBlockerCount: digest.releaseBlockerCount,
              topGapIds: digest.topGaps.map((gap) => gap.id),
              nextAction: digest.nextAction.action,
              nextMilestoneTitle: digest.nextMilestoneTitle,
            }));
            """
        )

        self.assertEqual(payload["status"], "open")
        self.assertEqual(payload["title"], "发布候选版还差 4 项")
        self.assertEqual(payload["releaseBlockerCount"], 4)
        self.assertEqual(payload["topGapIds"], ["reachable_scenes", "release_assets", "regression", "exported"])
        self.assertEqual(payload["nextAction"], "switch-screen")
        self.assertEqual(payload["nextMilestoneTitle"], "发布候选版")

    def test_project_milestone_gap_digest_marks_release_candidate_ready(self) -> None:
        payload = self.run_module_script(
            """
            const plan = tools.buildProjectMilestonePlan({
              totalChapters: 3,
              totalScenes: 6,
              scenesWithContent: 6,
              scenesWithBackground: 6,
              scenesWithMusic: 5,
              scenesWithEffects: 3,
              totalDialogueCount: 30,
              voicedDialogueCount: 22,
              readyAssetCount: 29,
              totalAssetCount: 30,
              validationErrorCount: 0,
              validationWarningCount: 0,
              brokenRoutes: 0,
              orphanScenes: 0,
              hasStarterKit: true,
              hasExport: true,
              regressionPass: true,
            });
            const digest = tools.buildProjectMilestoneGapDigest(plan);
            process.stdout.write(JSON.stringify({
              status: digest.status,
              title: digest.title,
              topGapCount: digest.topGaps.length,
              releaseBlockerCount: digest.releaseBlockerCount,
            }));
            """
        )

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["title"], "发布候选核心条件已达标")
        self.assertEqual(payload["topGapCount"], 0)
        self.assertEqual(payload["releaseBlockerCount"], 0)

    def test_project_milestones_are_exported_in_release_reports(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("function serializeProjectMilestonePlan", source)
        self.assertIn("function serializeProjectMilestoneGapDigest", source)
        self.assertIn("function buildReleaseReportNextStep", source)
        self.assertIn("function formatReleaseReportNextStepActionHint", source)
        self.assertIn("function formatReleaseReportNextStepAdvice", source)
        self.assertIn("gapDigest: serializeProjectMilestoneGapDigest(projectMilestoneGapDigest)", source)
        self.assertIn("const nextStep = buildReleaseReportNextStep(releaseFixOrder, projectMilestoneGapDigest);", source)
        self.assertIn("action: serializeReleaseReportAction(action)", source)
        self.assertIn('source: "project_milestone_gap"', source)
        self.assertIn("建议按钮：${actionLabel}", source)
        self.assertIn("formatReleaseReportNextStepAdvice(nextStep)", source)
        self.assertIn("buildProjectMilestoneGapDigest(projectMilestonePlan)", source)
        self.assertIn("## 成品目标路线", source)
        self.assertIn("成品目标路线：", source)
        self.assertIn("优先缺口：", source)
        self.assertIn("projectMilestoneGapTable", source)
        self.assertIn("formatProjectMilestonePrimaryBlocker", source)

    def test_project_milestones_are_visible_from_inspection_overview(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("function renderDashboardActionBrief", source)
        self.assertIn("${renderDashboardActionBrief(routeOverview)}", source)
        self.assertIn("creator-focus-panel", source)
        self.assertIn("今日工作台", source)
        self.assertIn("function dedupeDashboardActionBriefActions", source)
        self.assertIn('label: "重新导出网页包", action: "export-build", dataset: { "export-target": "web" }', source)
        self.assertIn("secondaryActions: secondaryActions.slice(0, 2)", source)
        self.assertIn("人工长流程试玩", source)
        self.assertIn("function renderCompactProjectMilestonePanel", source)
        self.assertIn("project-milestone-compact-panel", source)
        self.assertIn("function renderProjectMilestoneGapDigest", source)
        self.assertIn("project-milestone-gap-digest", source)
        self.assertIn("当前阶段缺口", source)
        self.assertIn("发布候选差距", source)
        self.assertIn('label: "去试玩确认", action: "switch-screen", screen: "preview"', source)
        self.assertIn("回首页看完整路线", source)
        self.assertIn("${renderCompactProjectMilestonePanel(routeOverview)}", source)

    def test_project_milestone_cards_follow_theme_surface_rules(self) -> None:
        source = STYLE_PATH.read_text(encoding="utf-8")
        creator_focus_styles = source.split(".creator-focus-panel {", 1)[1].split(".recent-work-panel", 1)[0]

        self.assertIn(".creator-focus-panel", source)
        self.assertIn(".creator-focus-layout", source)
        self.assertIn(".creator-focus-checklist", source)
        self.assertIn(".project-milestone-card,", source)
        self.assertIn(".project-milestone-gap-digest,", source)
        self.assertIn(".project-milestone-check,", source)
        self.assertIn(".project-milestone-gap-item,", source)
        self.assertIn(".project-milestone-card.is-good", source)
        self.assertIn(".project-milestone-gap-digest.is-ready", source)
        self.assertNotIn("radial-gradient", creator_focus_styles)
        self.assertNotIn("clamp(", creator_focus_styles)
        self.assertIn("letter-spacing: 0;", creator_focus_styles)
        self.assertIn(".project-milestone-card.is-warn", source)
        self.assertIn(".project-milestone-gap-digest.is-close", source)
        self.assertIn(".project-milestone-card.is-danger", source)
        self.assertIn(".project-milestone-card:hover", source)

    def test_project_milestones_are_visible_from_preview_summary(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        summary_start = source.index("function renderProjectValidationSummary()")
        summary_end = source.index("function getValidationIssueRecovery", summary_start)
        summary_source = source[summary_start:summary_end]

        self.assertIn("const routeOverview = buildSceneRouteOverview();", summary_source)
        self.assertIn("${renderCompactProjectMilestonePanel(routeOverview)}", summary_source)
        self.assertLess(
            summary_source.index("${renderEditorModeGuideCard(\"preview\")}"),
            summary_source.index("${renderCompactProjectMilestonePanel(routeOverview)}"),
        )
        self.assertLess(
            summary_source.index("${renderCompactProjectMilestonePanel(routeOverview)}"),
            summary_source.index("${renderReleaseSettingsPanel()}"),
        )


if __name__ == "__main__":
    unittest.main()
