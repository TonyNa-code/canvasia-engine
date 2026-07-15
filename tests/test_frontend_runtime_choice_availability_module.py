from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CONDITION_MODULE = ROOT_DIR / "export_player_template" / "runtime_conditions.js"
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_choice_availability.js"


class FrontendRuntimeChoiceAvailabilityModuleTests(unittest.TestCase):
    def test_resolves_hidden_locked_and_safety_options(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(CONDITION_MODULE))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaRuntimeChoiceAvailability;
            const options = [
              {{ id: "always", text: "继续", choiceAvailabilityMode: "always" }},
              {{ id: "secret", text: "秘密路线", choiceAvailabilityMode: "hide_when_false", choiceAvailabilityWhen: [{{ variableId: "affection", operator: ">=", value: 5 }}] }},
              {{ id: "locked", text: "回忆", choiceAvailabilityMode: "disable_when_false", choiceLockedReason: "还没有拿到钥匙", choiceAvailabilityWhen: [{{ variableId: "has_key", operator: "==", value: true }}] }},
            ];
            const normal = tools.resolveChoiceOptions(options, {{ affection: 3, has_key: false }});
            const unlocked = tools.resolveChoiceOptions(options, {{ affection: 6, has_key: true }});
            const deadEnd = tools.resolveChoiceOptions(options.slice(1), {{ affection: 0, has_key: false }});
            process.stdout.write(JSON.stringify({{
              normal,
              unlocked,
              deadEnd,
              nextIndex: tools.findSelectableChoiceIndex(normal.runtimeOptions, 1, 1),
              previousIndex: tools.findSelectableChoiceIndex(normal.runtimeOptions, 2, -1),
            }}));
            """
        )
        completed = subprocess.run(["node", "-e", script], cwd=ROOT_DIR, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual([option["id"] for option in payload["normal"]["runtimeOptions"]], ["always", "locked"])
        self.assertFalse(payload["normal"]["runtimeOptions"][1]["choiceEnabled"])
        self.assertEqual(payload["normal"]["runtimeOptions"][1]["choiceLockedReason"], "还没有拿到钥匙")
        self.assertEqual([option["id"] for option in payload["unlocked"]["runtimeOptions"]], ["always", "secret", "locked"])
        self.assertTrue(payload["deadEnd"]["allUnavailable"])
        self.assertEqual(payload["deadEnd"]["runtimeOptions"][-1]["id"], "__canvasia_choice_safety_continue__")
        self.assertEqual(payload["nextIndex"], 0)
        self.assertEqual(payload["previousIndex"], 0)


if __name__ == "__main__":
    unittest.main()
