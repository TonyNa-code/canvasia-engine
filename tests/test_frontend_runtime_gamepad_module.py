from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_gamepad.js"


def run_node_module(script_body: str) -> dict:
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
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


class FrontendRuntimeGamepadModuleTests(unittest.TestCase):
    def test_button_and_axis_actions_only_fire_on_press_edges(self) -> None:
        payload = run_node_module(
            """
            const button = (pressed = false) => ({ pressed, value: pressed ? 1 : 0 });
            const pad = {
              id: "Wireless Controller",
              index: 0,
              connected: true,
              buttons: Array.from({ length: 16 }, () => button()),
              axes: [0, 0],
            };
            pad.buttons[0] = button(true);
            const first = tools.translateRuntimeGamepads([pad]);
            const held = tools.translateRuntimeGamepads([pad], first.state);
            pad.buttons[0] = button(false);
            const released = tools.translateRuntimeGamepads([pad], held.state);
            pad.axes = [0.82, 0];
            const axisFirst = tools.translateRuntimeGamepads([pad], released.state);
            const axisHeld = tools.translateRuntimeGamepads([pad], axisFirst.state);
            pad.axes = [0, 0];
            const centered = tools.translateRuntimeGamepads([pad], axisHeld.state);
            pad.axes = [0.9, 0];
            const axisRepeated = tools.translateRuntimeGamepads([pad], centered.state);
            process.stdout.write(JSON.stringify({
              first: first.actions,
              held: held.actions,
              released: released.actions,
              axisFirst: axisFirst.actions,
              axisHeld: axisHeld.actions,
              centered: centered.actions,
              axisRepeated: axisRepeated.actions,
              status: axisRepeated.status,
            }));
            """
        )

        self.assertEqual(payload["first"], ["confirm"])
        self.assertEqual(payload["held"], [])
        self.assertEqual(payload["released"], [])
        self.assertEqual(payload["axisFirst"], ["right"])
        self.assertEqual(payload["axisHeld"], [])
        self.assertEqual(payload["centered"], [])
        self.assertEqual(payload["axisRepeated"], ["right"])
        self.assertEqual(payload["status"]["connectedCount"], 1)

    def test_dpad_and_axis_do_not_emit_duplicate_navigation_actions(self) -> None:
        payload = run_node_module(
            """
            const buttons = Array.from({ length: 16 }, () => ({ pressed: false, value: 0 }));
            buttons[15] = { pressed: true, value: 1 };
            const result = tools.translateRuntimeGamepads([{
              id: "Standard Pad",
              index: 0,
              connected: true,
              buttons,
              axes: [0.8, 0],
            }]);
            process.stdout.write(JSON.stringify({ actions: result.actions }));
            """
        )

        self.assertEqual(payload["actions"], ["right"])

    def test_directional_focus_prefers_geometric_neighbor_and_wraps(self) -> None:
        payload = run_node_module(
            """
            const element = (id, left, top) => ({
              id,
              getBoundingClientRect() { return { left, top, width: 100, height: 40 }; },
            });
            const center = element("center", 100, 100);
            const right = element("right", 260, 102);
            const down = element("down", 104, 220);
            const candidates = [center, right, down];
            process.stdout.write(JSON.stringify({
              right: tools.chooseDirectionalFocusTarget(center, candidates, "right")?.id,
              down: tools.chooseDirectionalFocusTarget(center, candidates, "down")?.id,
              wrapped: tools.chooseDirectionalFocusTarget(right, candidates, "right")?.id,
            }));
            """
        )

        self.assertEqual(payload["right"], "right")
        self.assertEqual(payload["down"], "down")
        self.assertEqual(payload["wrapped"], "down")

    def test_confirm_target_ignores_focus_left_inside_a_hidden_overlay(self) -> None:
        payload = run_node_module(
            """
            const element = (id, hidden = false) => ({
              id,
              hidden,
              disabled: false,
              getAttribute() { return null; },
              closest() { return null; },
              getBoundingClientRect() { return { width: hidden ? 0 : 100, height: hidden ? 0 : 40 }; },
            });
            const hiddenStartButton = element("startButton", true);
            const continueButton = element("continueButton");
            const fallbackButton = element("fallbackButton");
            const root = {
              querySelectorAll() { return [hiddenStartButton, continueButton, fallbackButton]; },
            };
            const recovered = tools.chooseRuntimeGamepadConfirmTarget(
              root,
              [hiddenStartButton, continueButton],
              { documentRef: { activeElement: hiddenStartButton } },
            );
            const kept = tools.chooseRuntimeGamepadConfirmTarget(
              root,
              [fallbackButton],
              { documentRef: { activeElement: continueButton } },
            );
            process.stdout.write(JSON.stringify({ recovered: recovered?.id, kept: kept?.id }));
            """
        )

        self.assertEqual(payload["recovered"], "continueButton")
        self.assertEqual(payload["kept"], "continueButton")

    def test_controller_uses_adaptive_polling_and_reports_connection_changes(self) -> None:
        payload = run_node_module(
            """
            let clock = 0;
            let pads = [];
            const frames = [];
            const actions = [];
            const statuses = [];
            const listeners = new Map();
            const eventTarget = {
              addEventListener(name, handler) { listeners.set(name, handler); },
              removeEventListener(name) { listeners.delete(name); },
            };
            const controller = tools.createRuntimeGamepadController({
              eventTarget,
              getGamepads: () => pads,
              now: () => clock,
              requestFrame(callback) { frames.push(callback); return frames.length; },
              cancelFrame() {},
              onAction(action) { actions.push(action); },
              onStatusChange(status) { statuses.push(status.label); },
            });
            controller.start();
            clock = 100;
            controller.poll(clock);
            const idleActions = actions.length;
            pads = [{
              id: "Pad One",
              index: 0,
              connected: true,
              buttons: [{ pressed: true, value: 1 }],
              axes: [0, 0],
            }];
            clock = 101;
            controller.refresh();
            clock = 110;
            controller.poll(clock);
            const heldActions = actions.length;
            pads[0].buttons[0] = { pressed: false, value: 0 };
            clock = 140;
            controller.poll(clock);
            pads[0].buttons[0] = { pressed: true, value: 1 };
            clock = 180;
            controller.poll(clock);
            const connectedStatus = controller.getStatus();
            controller.stop();
            process.stdout.write(JSON.stringify({
              idleActions,
              heldActions,
              actions,
              statuses,
              connectedStatus,
              listenerCount: listeners.size,
              scheduledFrameCount: frames.length,
            }));
            """
        )

        self.assertEqual(payload["idleActions"], 0)
        self.assertEqual(payload["heldActions"], 1)
        self.assertEqual(payload["actions"], ["confirm", "confirm"])
        self.assertTrue(payload["connectedStatus"]["connected"])
        self.assertIn("1 个 · Pad One", payload["statuses"])
        self.assertEqual(payload["listenerCount"], 0)
        self.assertEqual(payload["scheduledFrameCount"], 1)

    def test_gamepad_adjusts_select_and_range_controls_without_moving_focus(self) -> None:
        payload = run_node_module(
            """
            class FakeEvent {
              constructor(type) { this.type = type; }
            }
            const selectEvents = [];
            const select = {
              tagName: "SELECT",
              selectedIndex: 0,
              options: [{}, {}, {}],
              dispatchEvent(event) { selectEvents.push(event.type); },
            };
            const rangeEvents = [];
            const range = {
              tagName: "INPUT",
              type: "range",
              value: 2,
              stepUp() { this.value += 1; },
              stepDown() { this.value -= 1; },
              dispatchEvent(event) { rangeEvents.push(event.type); },
            };
            const root = { contains(element) { return element === select || element === range; } };
            const selectChanged = tools.adjustRuntimeGamepadControl("right", root, {
              documentRef: { activeElement: select },
              EventCtor: FakeEvent,
            });
            const rangeChanged = tools.adjustRuntimeGamepadControl("left", root, {
              documentRef: { activeElement: range },
              EventCtor: FakeEvent,
            });
            const keyboardEvent = tools.buildRuntimeGamepadKeyboardEvent("Escape", range);
            keyboardEvent.preventDefault();
            process.stdout.write(JSON.stringify({
              selectChanged,
              selectedIndex: select.selectedIndex,
              selectEvents,
              rangeChanged,
              rangeValue: range.value,
              rangeEvents,
              keyboardEvent,
            }));
            """
        )

        self.assertTrue(payload["selectChanged"])
        self.assertEqual(payload["selectedIndex"], 1)
        self.assertEqual(payload["selectEvents"], ["change"])
        self.assertTrue(payload["rangeChanged"])
        self.assertEqual(payload["rangeValue"], 1)
        self.assertEqual(payload["rangeEvents"], ["input", "change"])
        self.assertTrue(payload["keyboardEvent"]["defaultPrevented"])

    def test_help_group_explains_current_controller_status(self) -> None:
        payload = run_node_module(
            """
            const status = tools.buildRuntimeGamepadStatus([{ id: "Pad", index: 0, connected: true }]);
            const group = tools.buildRuntimeGamepadControlGroup(status);
            process.stdout.write(JSON.stringify({ status, group }));
            """
        )

        self.assertTrue(payload["status"]["connected"])
        self.assertIn("已连接", payload["group"]["description"])
        self.assertEqual(len(payload["group"]["shortcuts"]), 4)


if __name__ == "__main__":
    unittest.main()
