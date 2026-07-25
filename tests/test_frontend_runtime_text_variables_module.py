from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_text_variables.js"


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


class FrontendRuntimeTextVariablesModuleTests(unittest.TestCase):
    def test_interpolation_and_input_sanitizing_share_one_contract(self) -> None:
        payload = run_node_module(
            """
            const variablesById = new Map([
              ["player_name", { id: "player_name", type: "string", defaultValue: "旅人" }],
              ["score", { id: "score", type: "number", defaultValue: 0 }],
              ["flag", { id: "flag", type: "boolean", defaultValue: false }],
            ]);
            process.stdout.write(JSON.stringify({
              normalized: tools.normalizeTextInputBlock({ prompt: " ", maxLength: 999, allowEmpty: true }),
              ids: tools.collectRuntimeTextVariableIds("你好，{{ player_name }}", ["{{score}}", "{{player_name}}"]),
              interpolated: tools.interpolateRuntimeText(
                "{{player_name}} 得分 {{score}}，{{unknown}}",
                { player_name: "小夏", score: 12 },
                { variablesById }
              ),
              fallback: tools.interpolateRuntimeText("欢迎 {{player_name}}", {}, { variablesById }),
              withoutUnknown: tools.interpolateRuntimeText("A{{missing}}B", {}, { variablesById, keepUnknown: false }),
              textValue: tools.sanitizeTextInputValue("  小夏  ", { maxLength: 8 }, variablesById.get("player_name")),
              numberValue: tools.sanitizeTextInputValue(" 12.5 ", { maxLength: 8 }, variablesById.get("score")),
              invalidNumber: tools.sanitizeTextInputValue("十二", { maxLength: 8 }, variablesById.get("score")),
              tooLong: tools.sanitizeTextInputValue("abcdef", { maxLength: 4 }, variablesById.get("player_name")),
              unsupported: tools.sanitizeTextInputValue("yes", { maxLength: 8 }, variablesById.get("flag")),
              globalReady: Boolean(globalThis.CanvasiaRuntimeTextVariables?.interpolateRuntimeText),
            }));
            """
        )

        self.assertEqual(payload["normalized"]["prompt"], "请输入内容")
        self.assertEqual(payload["normalized"]["maxLength"], 200)
        self.assertTrue(payload["normalized"]["allowEmpty"])
        self.assertEqual(payload["ids"], ["player_name", "score"])
        self.assertEqual(payload["interpolated"], "小夏 得分 12，{{unknown}}")
        self.assertEqual(payload["fallback"], "欢迎 旅人")
        self.assertEqual(payload["withoutUnknown"], "AB")
        self.assertEqual(payload["textValue"]["value"], "小夏")
        self.assertEqual(payload["numberValue"]["value"], 12.5)
        self.assertFalse(payload["invalidNumber"]["ok"])
        self.assertFalse(payload["tooLong"]["ok"])
        self.assertFalse(payload["unsupported"]["ok"])
        self.assertTrue(payload["globalReady"])


if __name__ == "__main__":
    unittest.main()
