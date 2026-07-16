from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_controls.js"


class FrontendRuntimeControlsModuleTests(unittest.TestCase):
    def run_module(self, script_body: str) -> dict:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};
            {script_body}
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_modal_escape_closes_only_the_first_active_layer(self) -> None:
        payload = self.run_module(
            """
            const closed = [];
            let prevented = 0;
            const event = {
              code: "Escape",
              target: {},
              preventDefault() { prevented += 1; },
            };
            const handled = tools.handleRuntimeModalKeydown(event, [
              { isOpen: false, close() { closed.push("inactive"); } },
              { isOpen: true, close() { closed.push("top"); } },
              { isOpen: true, close() { closed.push("under"); } },
            ]);
            process.stdout.write(JSON.stringify({ handled, closed, prevented }));
            """
        )

        self.assertTrue(payload["handled"])
        self.assertEqual(payload["closed"], ["top"])
        self.assertEqual(payload["prevented"], 1)

    def test_active_modal_swallows_background_shortcuts_but_preserves_form_input(self) -> None:
        payload = self.run_module(
            """
            let prevented = 0;
            const active = [{ isOpen: () => true, close() {} }];
            const backgroundHandled = tools.handleRuntimeModalKeydown(
              { code: "KeyR", target: { kind: "background" }, preventDefault() { prevented += 1; } },
              active,
              (target) => target.kind === "input"
            );
            const inputHandled = tools.handleRuntimeModalKeydown(
              { code: "ArrowRight", target: { kind: "input" }, preventDefault() { prevented += 1; } },
              active,
              (target) => target.kind === "input"
            );
            const noModalHandled = tools.handleRuntimeModalKeydown(
              { code: "KeyR", target: {}, preventDefault() { prevented += 1; } },
              [{ isOpen: false, close() {} }]
            );
            process.stdout.write(JSON.stringify({ backgroundHandled, inputHandled, noModalHandled, prevented }));
            """
        )

        self.assertTrue(payload["backgroundHandled"])
        self.assertTrue(payload["inputHandled"])
        self.assertFalse(payload["noModalHandled"])
        self.assertEqual(payload["prevented"], 1)

    def test_operation_guide_renderer_escapes_project_supplied_text(self) -> None:
        payload = self.run_module(
            """
            const html = tools.renderOperationGuideGroups([{
              title: "<Guide>",
              description: "Use & learn",
              shortcuts: [{ keys: ["<A>"], label: "Go >", detail: "Safe & sound" }],
            }]);
            process.stdout.write(JSON.stringify({ html }));
            """
        )

        self.assertIn("&lt;Guide&gt;", payload["html"])
        self.assertIn("Use &amp; learn", payload["html"])
        self.assertIn("&lt;A&gt;", payload["html"])
        self.assertNotIn("<Guide>", payload["html"])


if __name__ == "__main__":
    unittest.main()
