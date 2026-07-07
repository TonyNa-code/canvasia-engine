from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "api_endpoints.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"


class FrontendApiEndpointsModuleTests(unittest.TestCase):
    def test_api_endpoints_are_centralized_and_override_openai_asset_endpoint(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{
              window: {{
                CanvasiaEditorOpenAiAssetGenerator: {{
                  API_GENERATE_OPENAI_ASSET: "/api/custom-openai-asset",
                }},
              }},
            }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorApiEndpoints;
            const result = {{
              keys: Object.keys(tools).sort(),
              endpointKeys: Object.keys(tools.API_ENDPOINTS).sort(),
              projectData: tools.API_PROJECT_DATA,
              saveScene: tools.API_SAVE_SCENE,
              generateOpenAiAsset: tools.API_GENERATE_OPENAI_ASSET,
              defaultGenerateOpenAiAsset: tools.DEFAULT_API_ENDPOINTS.generateOpenAiAsset,
              fallback: tools.getApiEndpoint("missing", "/fallback"),
              directLookup: tools.getApiEndpoint("creativeAssistant"),
              frozen: [
                Object.isFrozen(tools),
                Object.isFrozen(tools.API_ENDPOINTS),
                Object.isFrozen(tools.DEFAULT_API_ENDPOINTS),
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
        self.assertIn("API_PROJECT_DATA", payload["keys"])
        self.assertIn("API_CREATIVE_ASSISTANT", payload["keys"])
        self.assertIn("createProjectHistorySnapshot", payload["endpointKeys"])
        self.assertIn("importLocalizationPatches", payload["endpointKeys"])
        self.assertEqual(payload["projectData"], "/api/project-data")
        self.assertEqual(payload["saveScene"], "/api/save-scene")
        self.assertEqual(payload["generateOpenAiAsset"], "/api/custom-openai-asset")
        self.assertEqual(payload["defaultGenerateOpenAiAsset"], "/api/generate-openai-asset")
        self.assertEqual(payload["fallback"], "/fallback")
        self.assertEqual(payload["directLookup"], "/api/creative-assistant")
        self.assertEqual(payload["frozen"], [True, True, True])

    def test_editor_app_consumes_api_endpoint_module(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("const editorApiEndpointTools = window.CanvasiaEditorApiEndpoints;", app_source)
        self.assertIn("API_IMPORT_LOCALIZATION_PATCHES,", app_source)
        self.assertNotIn('const API_PROJECT_DATA = "/api/project-data";', app_source)
        self.assertNotIn('const API_IMPORT_LOCALIZATION_PATCHES = "/api/import-localization-patches"', app_source)


if __name__ == "__main__":
    unittest.main()
