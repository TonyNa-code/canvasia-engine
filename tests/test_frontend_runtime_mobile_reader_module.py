from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_mobile_reader.js"


class FrontendRuntimeMobileReaderModuleTests(unittest.TestCase):
    def test_mobile_reader_detects_devices_classifies_vertical_gestures_and_respects_mode(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};
            const targetListeners = new Map();
            const windowListeners = new Map();
            const documentListeners = new Map();
            const modeChanges = [];
            const gestures = [];
            const rootStyles = {{}};
            let mode = "auto";
            const nonInteractiveTarget = {{ closest: () => null }};
            const fakeGlobal = {{
              innerWidth: 390,
              innerHeight: 844,
              navigator: {{ maxTouchPoints: 5 }},
              visualViewport: {{
                width: 390,
                height: 780,
                addEventListener: (name, listener) => windowListeners.set(`visual:${{name}}`, listener),
                removeEventListener: (name) => windowListeners.delete(`visual:${{name}}`),
              }},
              matchMedia: (query) => ({{
                matches: query.includes("pointer: coarse") || query.includes("hover: none"),
                addEventListener() {{}},
                removeEventListener() {{}},
              }}),
              addEventListener: (name, listener) => windowListeners.set(name, listener),
              removeEventListener: (name) => windowListeners.delete(name),
            }};
            const fakeDocument = {{
              addEventListener: (name, listener) => documentListeners.set(name, listener),
              removeEventListener: (name) => documentListeners.delete(name),
            }};
            const gestureTarget = {{
              addEventListener: (name, listener) => targetListeners.set(name, listener),
              removeEventListener: (name) => targetListeners.delete(name),
            }};
            const controller = tools.createMobileReaderController({{
              root: {{ style: {{ setProperty: (key, value) => {{ rootStyles[key] = value; }} }} }},
              gestureTarget,
              globalObject: fakeGlobal,
              documentRef: fakeDocument,
              getMode: () => mode,
              onModeChange: (status) => modeChanges.push({{ active: status.active, reason: status.reason }}),
              onGesture: (gesture) => gestures.push(gesture),
            }});
            const started = controller.start();
            targetListeners.get("pointerdown")({{
              isPrimary: true,
              pointerId: 3,
              pointerType: "touch",
              clientX: 180,
              clientY: 520,
              timeStamp: 100,
              target: nonInteractiveTarget,
            }});
            targetListeners.get("pointerup")({{
              pointerId: 3,
              clientX: 184,
              clientY: 390,
              timeStamp: 320,
              preventDefault() {{}},
            }});
            mode = "off";
            const disabled = controller.refresh("setting");
            controller.stop();
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              environment: tools.detectMobileReaderEnvironment(fakeGlobal),
              started,
              disabled,
              modeChanges,
              gestures,
              rootStyles,
              up: tools.classifyMobileReaderGesture(
                {{ x: 20, y: 160, timeMs: 0 }},
                {{ x: 22, y: 80, timeMs: 220 }}
              ),
              down: tools.classifyMobileReaderGesture(
                {{ x: 20, y: 80, timeMs: 0 }},
                {{ x: 22, y: 160, timeMs: 220 }}
              ),
              horizontal: tools.classifyMobileReaderGesture(
                {{ x: 20, y: 80, timeMs: 0 }},
                {{ x: 160, y: 86, timeMs: 220 }}
              ),
              invalidMode: tools.getSafeMobileReaderMode("unexpected"),
              guide: tools.buildMobileReaderControlGroup({{ active: true }}),
            }}));
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
        payload = json.loads(completed.stdout)
        self.assertIn("createMobileReaderController", payload["keys"])
        self.assertTrue(payload["environment"]["touchCapable"])
        self.assertTrue(payload["started"]["active"])
        self.assertFalse(payload["disabled"]["active"])
        self.assertEqual(payload["gestures"], ["history"])
        self.assertEqual(payload["up"], "history")
        self.assertEqual(payload["down"], "dialog")
        self.assertEqual(payload["horizontal"], "")
        self.assertEqual(payload["invalidMode"], "auto")
        self.assertEqual(payload["rootStyles"]["--runtime-mobile-viewport-height"], "780px")
        self.assertIn("底部触控栏", payload["guide"]["shortcuts"][-1]["keys"])


if __name__ == "__main__":
    unittest.main()
