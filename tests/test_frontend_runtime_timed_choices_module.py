from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_timed_choices.js"


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


class FrontendRuntimeTimedChoicesModuleTests(unittest.TestCase):
    def test_config_target_and_persisted_state_are_sanitized(self) -> None:
        payload = run_node_module(
            """
            const disabled = tools.sanitizeTimedChoiceConfig({ timeoutSeconds: 0 });
            const minimum = tools.sanitizeTimedChoiceConfig({ timeoutSeconds: 0.2 });
            const maximum = tools.sanitizeTimedChoiceConfig({
              choiceTimeoutSeconds: 900,
              choiceTimeoutOptionId: " locked ",
            });
            const options = [
              { id: "hidden", choiceVisible: false },
              { id: "locked", choiceEnabled: false },
              { id: "safe", choiceEnabled: true },
            ];
            const target = tools.resolveTimedChoiceTarget(options, "locked");
            const state = tools.sanitizeTimedChoiceState({
              choiceKey: " scene:choice ",
              targetOptionId: " safe ",
              remainingMs: 999999,
            }, { timeoutSeconds: 12 });
            process.stdout.write(JSON.stringify({ disabled, minimum, maximum, target, state }));
            """
        )

        self.assertFalse(payload["disabled"]["enabled"])
        self.assertEqual(payload["minimum"]["timeoutSeconds"], 1)
        self.assertEqual(payload["maximum"]["timeoutSeconds"], 300)
        self.assertEqual(payload["maximum"]["timeoutOptionId"], "locked")
        self.assertEqual(payload["target"], "safe")
        self.assertEqual(payload["state"]["choiceKey"], "scene:choice")
        self.assertEqual(payload["state"]["remainingMs"], 12000)

    def test_controller_pauses_resumes_and_times_out_once(self) -> None:
        payload = run_node_module(
            """
            let now = 0;
            let scheduled = null;
            const timeoutEvents = [];
            const controller = tools.createTimedChoiceController({
              now: () => now,
              setInterval: (callback) => { scheduled = callback; return 1; },
              clearInterval: () => { scheduled = null; },
              onTimeout: (optionId, snapshot) => timeoutEvents.push({ optionId, snapshot }),
            });
            const started = controller.start({
              choiceKey: "scene:choice",
              block: { timeoutSeconds: 10, timeoutOptionId: "locked" },
              choiceOptions: [
                { id: "locked", choiceEnabled: false },
                { id: "safe", choiceEnabled: true },
              ],
            });
            now = 2500;
            controller.tick();
            const beforePause = controller.snapshot();
            const paused = controller.setPaused(true);
            now = 8000;
            controller.tick();
            const whilePaused = controller.snapshot();
            const resumed = controller.setPaused(false);
            now = 15500;
            controller.tick();
            controller.tick();
            const expired = controller.snapshot();
            process.stdout.write(JSON.stringify({
              started,
              beforePause,
              paused,
              whilePaused,
              resumed,
              expired,
              timeoutEvents,
              serialized: controller.serialize(),
              hasScheduledTimer: scheduled !== null,
            }));
            """
        )

        self.assertEqual(payload["started"]["targetOptionId"], "safe")
        self.assertEqual(payload["beforePause"]["remainingMs"], 7500)
        self.assertTrue(payload["paused"]["paused"])
        self.assertEqual(payload["whilePaused"]["remainingMs"], 7500)
        self.assertFalse(payload["resumed"]["paused"])
        self.assertFalse(payload["expired"]["active"])
        self.assertTrue(payload["expired"]["expired"])
        self.assertEqual(payload["expired"]["remainingMs"], 0)
        self.assertEqual(len(payload["timeoutEvents"]), 1)
        self.assertEqual(payload["timeoutEvents"][0]["optionId"], "safe")
        self.assertEqual(payload["serialized"]["remainingMs"], 0)
        self.assertFalse(payload["hasScheduledTimer"])


if __name__ == "__main__":
    unittest.main()
