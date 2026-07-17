from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_key_bindings import (
    DEFAULT_RUNTIME_KEY_BINDINGS as NATIVE_DEFAULT_RUNTIME_KEY_BINDINGS,
    RESERVED_RUNTIME_KEY_CODES as NATIVE_RESERVED_RUNTIME_KEY_CODES,
)


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

    def test_player_shortcuts_are_not_blocked_by_focused_buttons(self) -> None:
        source = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        start = source.index("function isKeyboardTypingTarget")
        end = source.index("\n}", start) + 2
        function_source = source[start:end]

        self.assertIn("input, textarea, select", function_source)
        self.assertNotIn("select, button", function_source)

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

    def test_key_bindings_sanitize_invalid_and_reserved_codes(self) -> None:
        payload = self.run_module(
            """
            const bindings = tools.sanitizeRuntimeKeyBindings({
              advance: "Escape",
              system: "KeyB",
              rollback: "NotARealCode",
              auto: "Digit7",
            });
            process.stdout.write(JSON.stringify({ bindings }));
            """
        )

        self.assertEqual(payload["bindings"]["advance"], "Space")
        self.assertEqual(payload["bindings"]["system"], "KeyB")
        self.assertEqual(payload["bindings"]["rollback"], "PageUp")
        self.assertEqual(payload["bindings"]["auto"], "Digit7")

    def test_web_and_native_key_binding_contracts_stay_aligned(self) -> None:
        payload = self.run_module(
            """
            process.stdout.write(JSON.stringify({
              defaults: tools.DEFAULT_RUNTIME_KEY_BINDINGS,
              reserved: [...tools.RESERVED_RUNTIME_KEY_CODES].sort(),
            }));
            """
        )

        self.assertEqual(payload["defaults"], NATIVE_DEFAULT_RUNTIME_KEY_BINDINGS)
        self.assertEqual(payload["reserved"], sorted(NATIVE_RESERVED_RUNTIME_KEY_CODES))

    def test_key_binding_conflicts_swap_instead_of_disabling_an_action(self) -> None:
        payload = self.run_module(
            """
            const result = tools.assignRuntimeKeyBinding({}, "hide", "KeyA");
            process.stdout.write(JSON.stringify({
              result,
              hideAction: tools.getRuntimeActionForCode(result.bindings, "KeyA"),
              previousHideAction: tools.getRuntimeActionForCode(result.bindings, "KeyU"),
            }));
            """
        )

        self.assertTrue(payload["result"]["changed"])
        self.assertEqual(payload["result"]["displacedAction"], "auto")
        self.assertEqual(payload["hideAction"], "hide")
        self.assertEqual(payload["previousHideAction"], "auto")

    def test_dynamic_guide_and_binding_rows_use_current_safe_labels(self) -> None:
        payload = self.run_module(
            """
            const groups = tools.buildRuntimeShortcutGroups({ advance: "KeyB", hide: "Digit4" });
            const rows = tools.renderRuntimeKeyBindingRows(
              { advance: "KeyB", hide: "Digit4" },
              { captureAction: "hide" }
            );
            process.stdout.write(JSON.stringify({ groups, rows }));
            """
        )

        self.assertEqual(payload["groups"][0]["shortcuts"][0]["keys"][0], "B")
        self.assertIn("请按新按键", payload["rows"])
        self.assertIn('data-runtime-key-binding="advance"', payload["rows"])
        self.assertIn('aria-pressed="true"', payload["rows"])

    def test_key_binding_controller_captures_persists_and_resets(self) -> None:
        payload = self.run_module(
            """
            const listeners = {};
            const list = {
              innerHTML: "",
              addEventListener(kind, callback) { listeners[`list:${kind}`] = callback; },
            };
            const documentRef = {
              addEventListener(kind, callback) { listeners[`document:${kind}`] = callback; },
            };
            const summary = { textContent: "" };
            const status = { textContent: "" };
            const resetButton = {
              disabled: false,
              addEventListener(kind, callback) { listeners[`reset:${kind}`] = callback; },
            };
            let bindings = tools.sanitizeRuntimeKeyBindings();
            let persisted = 0;
            let changed = 0;
            const controller = tools.createRuntimeKeyBindingController({
              refs: { list, summary, status, resetButton },
              documentRef,
              getBindings: () => bindings,
              setBindings: (next) => { bindings = next; },
              persist: () => { persisted += 1; },
              onChanged: () => { changed += 1; },
            });
            controller.attach();
            controller.render();
            listeners["list:click"]({
              target: { closest: () => ({ dataset: { runtimeKeyBinding: "hide" } }) },
            });
            listeners["document:keydown"]({
              code: "KeyB",
              preventDefault() {},
              stopImmediatePropagation() {},
            });
            const customized = { ...bindings, summary: summary.textContent, status: status.textContent };
            listeners["reset:click"]();
            process.stdout.write(JSON.stringify({ customized, reset: bindings, persisted, changed }));
            """
        )

        self.assertEqual(payload["customized"]["hide"], "KeyB")
        self.assertIn("已自定义 1 项", payload["customized"]["summary"])
        self.assertIn("已更新", payload["customized"]["status"])
        self.assertEqual(payload["reset"]["hide"], "KeyU")
        self.assertEqual(payload["persisted"], 2)
        self.assertEqual(payload["changed"], 2)


if __name__ == "__main__":
    unittest.main()
