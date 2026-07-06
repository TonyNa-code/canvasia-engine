from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "regression_diagnostics.js"


class FrontendRegressionDiagnosticsModuleTests(unittest.TestCase):
    def run_regression_diagnostics_script(self, body: str) -> dict:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorRegressionDiagnostics;
            {body}
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

    def test_regression_diagnostics_compacts_variable_and_condition_traces(self) -> None:
        payload = self.run_regression_diagnostics_script(
            """
            const caseResult = {
              variableOverrideSummary: "好感度=3 / route=common",
              conditionTraceSummaries: [
                "条件判断：命中分支 1 -> 教室；好感度 当前 3 >= 2：通过",
                "条件判断：命中否则 -> Missing；路线 当前 common contains good：失败",
                "额外条件：这个应该被 maxItems 截断",
              ],
            };
            process.stdout.write(JSON.stringify({
              keys: Object.keys(tools).sort(),
              line: tools.formatRegressionDiagnosticLine(caseResult, { maxItems: 2 }),
              conditionOnly: tools.formatRegressionDiagnosticLine(caseResult, { includeVariable: false, maxItems: 1 }),
              compact: tools.formatRegressionDiagnosticLine(caseResult, { maxItems: 2, maxLength: 28 }),
              serialized: tools.serializeRegressionDiagnostics(caseResult, { maxItems: 2 }),
              empty: tools.serializeRegressionDiagnostics({}),
            }));
            """
        )

        self.assertIn("formatRegressionDiagnosticLine", payload["keys"])
        self.assertIn("测试预设：好感度=3", payload["line"])
        self.assertIn("命中分支 1", payload["line"])
        self.assertNotIn("额外条件", payload["line"])
        self.assertNotIn("测试预设", payload["conditionOnly"])
        self.assertTrue(payload["compact"].endswith("…"))
        self.assertTrue(payload["serialized"]["hasDiagnostics"])
        self.assertEqual(len(payload["serialized"]["conditionTraceSummaries"]), 2)
        self.assertFalse(payload["empty"]["hasDiagnostics"])


if __name__ == "__main__":
    unittest.main()
