from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_mobile_reader_ui.js"


class FrontendRuntimeMobileReaderUiModuleTests(unittest.TestCase):
    def test_mobile_reader_ui_owns_dock_history_and_persisted_mode_workflow(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            class FakeElement {{
              constructor() {{
                this.hidden = false;
                this.disabled = false;
                this.attributes = {{}};
                this.classNames = new Set();
                this.strong = {{ text: "", replaceChildren: (value) => {{ this.strong.text = value; }} }};
                this.classList = {{
                  toggle: (name, active) => active ? this.classNames.add(name) : this.classNames.delete(name),
                }};
              }}
              setAttribute(name, value) {{ this.attributes[name] = value; }}
              querySelector(selector) {{ return selector === "strong" ? this.strong : null; }}
              closest(selector) {{ return selector === "[data-history-index]" ? this : null; }}
              focus() {{ this.focused = true; }}
            }}

            const listeners = new Map();
            const windowListeners = new Map();
            const root = new FakeElement();
            root.dataset = {{}};
            root.style = {{ setProperty() {{}} }};
            const fakeDocument = {{
              documentElement: root,
              addEventListener: (name, listener) => listeners.set(`document:${{name}}`, listener),
              removeEventListener: (name) => listeners.delete(`document:${{name}}`),
            }};
            const fakeGlobal = {{
              HTMLElement: FakeElement,
              innerWidth: 390,
              innerHeight: 844,
              navigator: {{ maxTouchPoints: 5 }},
              matchMedia: () => ({{ matches: true, addEventListener() {{}}, removeEventListener() {{}} }}),
              addEventListener: (name, listener) => windowListeners.set(name, listener),
              removeEventListener: (name) => windowListeners.delete(name),
            }};
            const stageFrame = new FakeElement();
            stageFrame.addEventListener = (name, listener) => listeners.set(name, listener);
            stageFrame.removeEventListener = (name) => listeners.delete(name);
            const refs = {{
              stageFrame,
              startOverlay: {{ hidden: true }},
              mobileReaderDock: new FakeElement(),
              mobileAutoButton: new FakeElement(),
              mobileDialogButton: new FakeElement(),
              mobileHistoryButton: new FakeElement(),
              mobileSystemButton: new FakeElement(),
              mobileHistorySheet: new FakeElement(),
              mobileHistoryList: {{ innerHTML: "" }},
              mobileHistoryCloseButton: new FakeElement(),
              menuMobileReaderModeSelect: {{ value: "" }},
            }};
            const state = {{
              started: true,
              session: {{ history: [{{ text: "hello" }}] }},
              playback: {{ mobileReaderMode: "auto", autoPlay: true }},
              dialogHidden: false,
              mobileReaderStatus: null,
              mobileHistoryOpen: false,
            }};
            let persisted = 0;
            let renderedPlayback = 0;
            let stoppedAuto = 0;
            let historyClicks = 0;
            const ui = tools.createMobileReaderUiController({{
              documentRef: fakeDocument,
              globalObject: fakeGlobal,
              refs,
              state,
              getSnapshot: () => ({{ type: "text" }}),
              getOverlayRoot: () => state.mobileHistoryOpen ? refs.mobileHistorySheet : null,
              renderHistory: () => "<article>history</article>",
              renderEmpty: (value) => value,
              handleHistoryPanelClick: () => {{ historyClicks += 1; }},
              stopAutoAdvance: () => {{ stoppedAuto += 1; }},
              persistPlaybackSettings: () => {{ persisted += 1; }},
              renderPlaybackControls: () => {{ renderedPlayback += 1; }},
            }});

            const started = ui.start();
            const dockVisibleAfterStart = !refs.mobileReaderDock.hidden;
            const historyOpened = ui.openHistory();
            const historyVisible = !refs.mobileHistorySheet.hidden;
            ui.handleHistorySheetClick({{ target: new (class extends FakeElement {{}})() }});
            ui.handleModeChange({{ target: {{ value: "off" }} }});
            ui.stop();

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              started,
              listenerCountAfterStop: listeners.size,
              dockVisibleAfterStart,
              historyOpened,
              historyVisible,
              historyOpen: state.mobileHistoryOpen,
              historyHtml: refs.mobileHistoryList.innerHTML,
              historyClicks,
              stoppedAuto,
              persisted,
              renderedPlayback,
              mode: state.playback.mobileReaderMode,
              dataset: root.dataset.runtimeMobileReader,
              autoLabel: refs.mobileAutoButton.strong.text,
              closeFocused: Boolean(refs.mobileHistoryCloseButton.focused),
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
        self.assertEqual(payload["keys"], ["createMobileReaderUiController"])
        self.assertTrue(payload["started"]["active"])
        self.assertEqual(payload["listenerCountAfterStop"], 0)
        self.assertTrue(payload["dockVisibleAfterStart"])
        self.assertTrue(payload["historyOpened"])
        self.assertTrue(payload["historyVisible"])
        self.assertFalse(payload["historyOpen"])
        self.assertEqual(payload["historyHtml"], "<article>history</article>")
        self.assertEqual(payload["historyClicks"], 1)
        self.assertEqual(payload["stoppedAuto"], 1)
        self.assertEqual(payload["persisted"], 1)
        self.assertEqual(payload["renderedPlayback"], 1)
        self.assertEqual(payload["mode"], "off")
        self.assertEqual(payload["dataset"], "inactive")
        self.assertEqual(payload["autoLabel"], "自动中")
        self.assertTrue(payload["closeFocused"])


if __name__ == "__main__":
    unittest.main()
