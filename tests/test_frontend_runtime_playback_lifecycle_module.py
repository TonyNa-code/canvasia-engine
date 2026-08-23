from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_playback_lifecycle.js"


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


class FrontendRuntimePlaybackLifecycleModuleTests(unittest.TestCase):
    def test_pause_aware_delay_preserves_remaining_time_and_replaces_stale_tasks(self) -> None:
        payload = run_node_module(
            """
            let now = 0;
            let nextTimerId = 1;
            const timers = new Map();
            const events = [];
            const controller = tools.createPauseAwareDelayController({
              now: () => now,
              setTimeout(callback, delayMs) {
                const id = nextTimerId++;
                timers.set(id, { callback, delayMs });
                return id;
              },
              clearTimeout(id) { timers.delete(id); },
            });
            controller.schedule({ key: "line-a", delayMs: 1000, callback: ({ key }) => events.push(key) });
            now = 400;
            const paused = controller.pause();
            now = 5000;
            const whilePaused = controller.getSnapshot();
            const resumed = controller.resume();
            const resumedTimer = Array.from(timers.values())[0];
            now = 5600;
            resumedTimer.callback();
            controller.pause();
            controller.schedule({ key: "stale", delayMs: 300, callback: () => events.push("stale") });
            controller.schedule({ key: "replacement", delayMs: 200, callback: () => events.push("replacement") });
            const scheduledWhilePaused = controller.getSnapshot();
            controller.resume();
            const replacementTimer = Array.from(timers.values())[0];
            replacementTimer.callback();
            process.stdout.write(JSON.stringify({
              paused,
              whilePaused,
              resumed,
              resumedDelayMs: resumedTimer.delayMs,
              scheduledWhilePaused,
              events,
              final: controller.getSnapshot(),
            }));
            """
        )

        self.assertTrue(payload["paused"]["paused"])
        self.assertEqual(payload["paused"]["remainingMs"], 600)
        self.assertEqual(payload["whilePaused"]["remainingMs"], 600)
        self.assertFalse(payload["resumed"]["paused"])
        self.assertEqual(payload["resumedDelayMs"], 600)
        self.assertEqual(payload["scheduledWhilePaused"]["key"], "replacement")
        self.assertEqual(payload["events"], ["line-a", "replacement"])
        self.assertFalse(payload["final"]["scheduled"])

    def test_document_lifecycle_waits_for_every_suspend_reason_before_resuming(self) -> None:
        payload = run_node_module(
            """
            class FakeTarget {
              constructor() { this.listeners = new Map(); }
              addEventListener(name, callback) {
                const callbacks = this.listeners.get(name) || [];
                callbacks.push(callback);
                this.listeners.set(name, callbacks);
              }
              removeEventListener(name, callback) {
                this.listeners.set(name, (this.listeners.get(name) || []).filter((item) => item !== callback));
              }
              emit(name) { for (const callback of this.listeners.get(name) || []) callback(); }
            }
            let now = 100;
            const documentRef = new FakeTarget();
            documentRef.hidden = false;
            const windowRef = new FakeTarget();
            const events = [];
            const lifecycle = tools.createDocumentPlaybackLifecycle({
              documentRef,
              windowRef,
              now: () => now,
              onSuspend: (snapshot) => events.push([snapshot.event, snapshot.reasons]),
              onResume: (snapshot) => events.push([snapshot.event, snapshot.lastSuspendedDurationMs]),
            });
            lifecycle.attach();
            windowRef.emit("blur");
            now = 300;
            documentRef.hidden = true;
            documentRef.emit("visibilitychange");
            windowRef.emit("focus");
            const stillHidden = lifecycle.getSnapshot();
            now = 900;
            documentRef.hidden = false;
            documentRef.emit("visibilitychange");
            const resumed = lifecycle.getSnapshot();
            lifecycle.detach();
            process.stdout.write(JSON.stringify({ events, stillHidden, resumed, detached: lifecycle.getSnapshot() }));
            """
        )

        self.assertEqual(payload["events"][0], ["suspend", ["blurred"]])
        self.assertTrue(payload["stillHidden"]["suspended"])
        self.assertEqual(payload["stillHidden"]["reasons"], ["hidden"])
        self.assertEqual(payload["events"][1], ["resume", 800])
        self.assertFalse(payload["resumed"]["suspended"])
        self.assertEqual(payload["resumed"]["totalSuspendedMs"], 800)
        self.assertFalse(payload["detached"]["attached"])


if __name__ == "__main__":
    unittest.main()
