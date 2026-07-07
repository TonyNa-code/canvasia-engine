from __future__ import annotations

import json
import re
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "module_guard.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"
INDEX_PATH = ROOT_DIR / "prototype_editor" / "index.html"
SCRIPT_SRC_PATTERN = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)


class FrontendModuleGuardModuleTests(unittest.TestCase):
    def test_module_guard_reports_missing_modules_with_readable_recovery(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const classListCalls = [];
            const focusCalls = [];
            const elements = {{
              loadingState: {{
                classList: {{ add: (value) => classListCalls.push(["loading", "add", value]) }},
              }},
              errorMessage: {{ textContent: "" }},
              reloadButton: {{
                focus: () => focusCalls.push("reload"),
              }},
              errorState: {{
                classList: {{ remove: (value) => classListCalls.push(["error", "remove", value]) }},
                querySelector: (selector) => selector === '[data-action="reload-editor-page"]' ? elements.reloadButton : null,
              }},
            }};
            const fakeDocument = {{
              getElementById: (id) => elements[id] ?? null,
            }};
            const context = {{ window: {{ document: fakeDocument }} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorModuleGuard;
            const required = tools.getRequiredEditorModules();
            const completeScope = Object.fromEntries(required.map((entry) => [entry.globalName, {{ ok: true }}]));
            const missingScope = {{ ...completeScope }};
            delete missingScope.CanvasiaEditorProjectCenter;
            delete missingScope.CanvasiaEditorCommandPalette;

            let thrown = null;
            try {{
              tools.assertRequiredModulesReady({{ scope: missingScope, document: fakeDocument }});
            }} catch (error) {{
              thrown = {{
                name: error.name,
                isEditorModuleLoadError: error.isEditorModuleLoadError,
                missing: error.missingModules.map((entry) => entry.globalName),
                message: error.message,
              }};
            }}

            const result = {{
              keyCount: required.length,
              first: required[0],
              last: required[required.length - 1],
              missingFromEmpty: tools.getMissingEditorModules({{}}).length,
              complete: tools.assertRequiredModulesReady({{ scope: completeScope, document: fakeDocument, focus: false }}),
              thrown,
              errorMessage: elements.errorMessage.textContent,
              classListCalls,
              focusCalls,
              frozen: [
                Object.isFrozen(tools),
                Object.isFrozen(tools.REQUIRED_EDITOR_MODULES),
                Object.isFrozen(tools.REQUIRED_EDITOR_MODULES[0]),
              ],
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
        self.assertGreaterEqual(payload["keyCount"], 80)
        self.assertEqual(payload["first"]["globalName"], "CanvasiaRuntimeConditions")
        self.assertEqual(payload["last"]["globalName"], "CanvasiaEditorCommandPalette")
        self.assertEqual(payload["missingFromEmpty"], payload["keyCount"])
        self.assertTrue(payload["complete"])
        self.assertEqual(payload["thrown"]["name"], "CanvasiaEditorModuleLoadError")
        self.assertTrue(payload["thrown"]["isEditorModuleLoadError"])
        self.assertEqual(
            payload["thrown"]["missing"],
            ["CanvasiaEditorProjectCenter", "CanvasiaEditorCommandPalette"],
        )
        self.assertIn("项目中心", payload["errorMessage"])
        self.assertIn("指挥面板", payload["errorMessage"])
        self.assertIn("请先刷新页面", payload["errorMessage"])
        self.assertIn(["loading", "add", "is-hidden"], payload["classListCalls"])
        self.assertIn(["error", "remove", "is-hidden"], payload["classListCalls"])
        self.assertEqual(payload["focusCalls"], ["reload"])
        self.assertEqual(payload["frozen"], [True, True, True])

    def test_editor_app_asserts_module_guard_before_using_globals(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")

        self.assertTrue(app_source.startswith("window.CanvasiaEditorModuleGuard?.assertRequiredModulesReady?.();"))
        self.assertLess(
            app_source.index("window.CanvasiaEditorModuleGuard?.assertRequiredModulesReady?.();"),
            app_source.index("const editorApiEndpointTools = window.CanvasiaEditorApiEndpoints;"),
        )

    def test_module_guard_requirements_match_editor_entrypoint_scripts(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const scripts = context.window.CanvasiaEditorModuleGuard
              .getRequiredEditorModules()
              .map((entry) => entry.script);
            process.stdout.write(JSON.stringify(scripts));
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
        required_scripts = json.loads(completed.stdout)
        entrypoint_scripts = SCRIPT_SRC_PATTERN.findall(INDEX_PATH.read_text(encoding="utf-8"))

        for script_path in required_scripts:
            self.assertIn(script_path, entrypoint_scripts)
        self.assertLess(entrypoint_scripts.index("./modules/command_palette.js"), entrypoint_scripts.index("./modules/module_guard.js"))
        self.assertLess(entrypoint_scripts.index("./modules/module_guard.js"), entrypoint_scripts.index("./app.js"))


if __name__ == "__main__":
    unittest.main()
