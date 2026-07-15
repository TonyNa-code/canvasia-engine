from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "export_report_descriptions.js"


class FrontendExportReportDescriptionsModuleTests(unittest.TestCase):
    def test_export_report_descriptions_explain_known_and_fallback_reports(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorExportReportDescriptions;
            const exportResult = {{
              target: "native_runtime",
              targetLabel: "原生 Runtime",
              routePlaytestReadinessPercent: 87,
              routePlaytestRouteCaseCount: 6,
              routePlaytestEndingCaseCount: 2,
              routePlaytestBlockedCaseCount: 1,
              releaseReadinessStatus: "needs_review",
              releaseReadinessScore: 82,
              playtestGuidePublicUrl: "/exports/demo/README.md?x=<unsafe>",
              releaseReadinessReportPublicUrl: "/exports/demo/readiness.md",
            }};
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              knownMarkdown: tools.describeExportReportFile("reports/performance-budget.md"),
              knownCsv: tools.describeExportReportFile("release-fix-order.csv"),
              knownReadme: tools.describeExportReportFile("README_试玩验收先看这里.md"),
              unknownJson: tools.describeExportReportFile("extra/custom-report.json"),
              unknownCsv: tools.describeExportReportFile("extra/custom-report.csv"),
              unknownMarkdown: tools.describeExportReportFile("extra/custom-report.md"),
              normalized: tools.normalizeReportLookupName(String.raw`nested\\path/report.md`),
              playable: tools.isPlayableExportResult(exportResult),
              nonPlayable: tools.isPlayableExportResult({{ target: "renpy" }}),
              links: tools.getLatestExportReportLinks(exportResult),
              panel: tools.renderLatestExportReportPanel(exportResult),
              emptyPanel: tools.renderLatestExportReportPanel({{ target: "renpy" }}),
              frozen: [
                Object.isFrozen(tools),
                Object.isFrozen(tools.REPORT_DESCRIPTION_BY_NAME),
                Object.isFrozen(tools.PLAYABLE_EXPORT_REPORT_LINKS),
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
        self.assertIn("describeExportReportFile", payload["keys"])
        self.assertIn("发布性能预算", payload["knownMarkdown"])
        self.assertIn("发布前修复顺序", payload["knownCsv"])
        self.assertIn("试玩验收入口", payload["knownReadme"])
        self.assertIn("机器可读", payload["unknownJson"])
        self.assertIn("表格", payload["unknownCsv"])
        self.assertIn("补充发布检查报告", payload["unknownMarkdown"])
        self.assertEqual(payload["normalized"], "report.md")
        self.assertTrue(payload["playable"])
        self.assertFalse(payload["nonPlayable"])
        self.assertEqual(len(payload["links"]), 2)
        self.assertTrue(payload["links"][0]["primary"])
        self.assertIn("最近导出的验收报告", payload["panel"])
        self.assertIn("87%", payload["panel"])
        self.assertIn("needs_review · 82 分", payload["panel"])
        self.assertIn("&lt;unsafe&gt;", payload["panel"])
        self.assertEqual(payload["emptyPanel"], "")
        self.assertEqual(payload["frozen"], [True, True, True])


if __name__ == "__main__":
    unittest.main()
