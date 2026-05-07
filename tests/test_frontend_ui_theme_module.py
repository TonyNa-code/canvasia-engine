from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "ui_theme.js"


class FrontendUiThemeModuleTests(unittest.TestCase):
    def test_ui_theme_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.TonyNaEditorUiTheme;
            const storage = {{
              values: new Map(),
              getItem(key) {{
                return this.values.has(key) ? this.values.get(key) : null;
              }},
              setItem(key, value) {{
                this.values.set(key, String(value));
              }},
            }};
            const failingStorage = {{
              getItem() {{
                throw new Error("blocked");
              }},
              setItem() {{
                throw new Error("blocked");
              }},
            }};

            const persisted = tools.persistStoredEditorUiThemeMode(storage, " dark ");
            const result = {{
              keys: Object.keys(tools).sort(),
              labels: [
                tools.getUiThemeModeLabel("auto"),
                tools.getUiThemeModeLabel("light"),
                tools.getUiThemeModeLabel("dark"),
                tools.getUiThemeModeLabel("broken"),
              ],
              safeModes: [
                tools.getSafeUiThemeMode(" dark "),
                tools.getSafeUiThemeMode("light"),
                tools.getSafeUiThemeMode("broken"),
                tools.getSafeUiThemeMode(null),
              ],
              resolved: [
                tools.resolveUiTheme("auto", new Date(2026, 0, 1, 8)),
                tools.resolveUiTheme("auto", new Date(2026, 0, 1, 22)),
                tools.resolveUiTheme("light", new Date(2026, 0, 1, 22)),
                tools.resolveUiTheme("dark", new Date(2026, 0, 1, 8)),
                tools.resolveUiTheme("broken", new Date("bad-date")),
              ],
              storageKey: tools.EDITOR_UI_THEME_STORAGE_KEY,
              persisted,
              savedMode: storage.getItem(tools.EDITOR_UI_THEME_STORAGE_KEY),
              loadedMode: tools.loadStoredEditorUiThemeMode(storage, "light"),
              fallbackMode: tools.loadStoredEditorUiThemeMode(null, "dark"),
              failingLoad: tools.loadStoredEditorUiThemeMode(failingStorage, "light"),
              failingPersist: tools.persistStoredEditorUiThemeMode(failingStorage, "light"),
            }};
            process.stdout.write(JSON.stringify(result));
            """
        )
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("resolveUiTheme", payload["keys"])
        self.assertIn("loadStoredEditorUiThemeMode", payload["keys"])
        self.assertEqual(payload["labels"], ["自动切换", "浅色模式", "深色模式", "自动切换"])
        self.assertEqual(payload["safeModes"], ["dark", "light", "auto", "auto"])
        self.assertEqual(payload["resolved"][:4], ["light", "dark", "light", "dark"])
        self.assertIn(payload["resolved"][4], ["light", "dark"])
        self.assertEqual(payload["storageKey"], "tony-na-engine:editor-ui-theme-mode")
        self.assertTrue(payload["persisted"])
        self.assertEqual(payload["savedMode"], "dark")
        self.assertEqual(payload["loadedMode"], "dark")
        self.assertEqual(payload["fallbackMode"], "dark")
        self.assertEqual(payload["failingLoad"], "light")
        self.assertFalse(payload["failingPersist"])


if __name__ == "__main__":
    unittest.main()
