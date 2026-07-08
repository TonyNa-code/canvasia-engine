from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from export_report_descriptions import REPORT_DESCRIPTION_BY_NAME, describe_export_report_file


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "export_report_descriptions.js"


def read_frontend_report_descriptions() -> dict[str, str]:
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        const vm = require("vm");
        const context = {{ window: {{}} }};
        context.globalThis = context;
        vm.createContext(context);
        vm.runInContext(fs.readFileSync({json.dumps(str(FRONTEND_MODULE_PATH))}, "utf8"), context);
        const tools = context.window.CanvasiaEditorExportReportDescriptions;
        process.stdout.write(JSON.stringify(tools.REPORT_DESCRIPTION_BY_NAME));
        """
    )
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


class ExportReportDescriptionParityTests(unittest.TestCase):
    def test_python_and_frontend_report_descriptions_stay_in_sync(self) -> None:
        self.assertEqual(read_frontend_report_descriptions(), REPORT_DESCRIPTION_BY_NAME)

    def test_backend_fallbacks_match_frontend_contract_examples(self) -> None:
        self.assertIn("发布性能预算", describe_export_report_file("nested/performance-budget.md"))
        self.assertIn("机器可读", describe_export_report_file("custom-extra-report.json"))
        self.assertIn("表格", describe_export_report_file("custom-extra-report.csv"))
        self.assertIn("补充发布检查报告", describe_export_report_file("custom-extra-report.md"))


if __name__ == "__main__":
    unittest.main()
