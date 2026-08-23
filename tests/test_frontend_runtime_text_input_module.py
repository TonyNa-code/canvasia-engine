from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_text_input.js"


class FrontendRuntimeTextInputModuleTests(unittest.TestCase):
    def test_controller_owns_dialog_lifecycle_validation_and_submission(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            function createRef() {{
              return {{
                listeners: new Map(),
                hidden: true,
                textContent: "",
                value: "",
                type: "text",
                maxLength: 0,
                placeholder: "",
                focusCount: 0,
                addEventListener(name, callback) {{ this.listeners.set(name, callback); }},
                removeEventListener(name) {{ this.listeners.delete(name); }},
                removeAttribute(name) {{ if (name === "maxlength") this.maxLength = -1; }},
                focus() {{ this.focusCount += 1; }},
              }};
            }}

            const refs = {{
              dialog: createRef(),
              form: createRef(),
              title: createRef(),
              summary: createRef(),
              label: createRef(),
              input: createRef(),
              error: createRef(),
              variable: createRef(),
              counter: createRef(),
            }};
            const variablesById = new Map([
              ["player_name", {{ id: "player_name", name: "玩家姓名", type: "string", defaultValue: "" }}],
            ]);
            const snapshot = {{
              blockType: "text_input",
              block: {{
                type: "text_input",
                variableId: "player_name",
                prompt: "请告诉我你的名字",
                placeholder: "输入姓名",
                maxLength: 6,
                allowEmpty: false,
              }},
              variables: {{}},
              visualState: {{}},
            }};
            let persistCount = 0;
            let stopCount = 0;
            let moveCount = 0;
            let renderCount = 0;
            const controller = tools.createRuntimeTextInputController({{
              refs,
              variablesById,
              windowRef: {{ requestAnimationFrame(callback) {{ callback(); return 1; }} }},
              getSnapshot: () => snapshot,
              getSnapshotKey: () => "scene_a:0",
              getLocalizedValue: (source, key, fallback) => source[key] || fallback,
              interpolateLocalizedText: (value) => value,
              normalizeValue: (_id, value) => value,
              persistVariables: () => {{ persistCount += 1; }},
              stopAutoAdvance: () => {{ stopCount += 1; }},
              moveForward: () => {{ moveCount += 1; }},
              render: () => {{ renderCount += 1; }},
            }});
            controller.attach();
            const synced = controller.sync(snapshot);
            const afterSync = {{
              state: controller.getState(),
              dialogHidden: refs.dialog.hidden,
              title: refs.title.textContent,
              label: refs.label.textContent,
              placeholder: refs.input.placeholder,
              maxLength: refs.input.maxLength,
              counter: refs.counter.textContent,
              focusCount: refs.input.focusCount,
            }};

            refs.input.value = "";
            const invalid = controller.submit({{ preventDefault() {{}} }});
            const invalidError = refs.error.textContent;
            refs.input.value = "小夏";
            refs.input.listeners.get("input")?.({{ target: refs.input }});
            const counterAfterInput = refs.counter.textContent;
            const submitted = controller.submit({{ preventDefault() {{}} }});
            const afterSubmit = {{
              state: controller.getState(),
              dialogHidden: refs.dialog.hidden,
              variables: snapshot.variables,
              visualState: snapshot.visualState,
              persistCount,
              stopCount,
              moveCount,
              renderCount,
            }};
            controller.detach();

            process.stdout.write(JSON.stringify({{
              exports: Object.keys(tools).sort(),
              synced,
              afterSync,
              invalid,
              invalidError,
              counterAfterInput,
              submitted,
              afterSubmit,
              detached: controller.getState().attached,
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
        self.assertEqual(payload["exports"], ["createRuntimeTextInputController"])
        self.assertTrue(payload["synced"])
        self.assertTrue(payload["afterSync"]["state"]["open"])
        self.assertFalse(payload["afterSync"]["dialogHidden"])
        self.assertEqual(payload["afterSync"]["title"], "请告诉我你的名字")
        self.assertEqual(payload["afterSync"]["label"], "玩家姓名")
        self.assertEqual(payload["afterSync"]["placeholder"], "输入姓名")
        self.assertEqual(payload["afterSync"]["maxLength"], 6)
        self.assertEqual(payload["afterSync"]["counter"], "0 / 6")
        self.assertGreaterEqual(payload["afterSync"]["focusCount"], 1)
        self.assertFalse(payload["invalid"])
        self.assertIn("请先填写", payload["invalidError"])
        self.assertEqual(payload["counterAfterInput"], "2 / 6")
        self.assertTrue(payload["submitted"])
        self.assertFalse(payload["afterSubmit"]["state"]["open"])
        self.assertTrue(payload["afterSubmit"]["dialogHidden"])
        self.assertEqual(payload["afterSubmit"]["variables"]["player_name"], "小夏")
        self.assertEqual(payload["afterSubmit"]["visualState"]["speakerName"], "玩家输入")
        self.assertIn("玩家姓名 已保存", payload["afterSubmit"]["visualState"]["dialogueText"])
        self.assertEqual(payload["afterSubmit"]["persistCount"], 1)
        self.assertEqual(payload["afterSubmit"]["stopCount"], 1)
        self.assertEqual(payload["afterSubmit"]["moveCount"], 1)
        self.assertEqual(payload["afterSubmit"]["renderCount"], 1)
        self.assertFalse(payload["detached"])


if __name__ == "__main__":
    unittest.main()
