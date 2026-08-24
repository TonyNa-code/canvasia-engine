from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "ui_kit_package.js"


class FrontendUiKitPackageModuleTests(unittest.TestCase):
    def run_node(self, body: str) -> dict:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const {{ webcrypto }} = require("crypto");
            const {{ TextEncoder }} = require("util");
            const context = {{
              window: {{
                crypto: webcrypto,
                TextEncoder,
                btoa: (binary) => Buffer.from(binary, "binary").toString("base64"),
              }},
            }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorUiKitPackage;
            (async () => {{
              {body}
            }})().catch((error) => {{
              process.stderr.write(String(error?.stack || error));
              process.exitCode = 1;
            }});
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
        return json.loads(completed.stdout)

    def test_build_validate_and_import_request_preserve_bindings_and_rights(self) -> None:
        payload = self.run_node(
            """
            const files = new Map([
              ["/panel.png", Buffer.from([137, 80, 78, 71, 1, 2, 3, 4])],
              ["/story.ttf", Buffer.from([0, 1, 0, 0, 5, 6, 7, 8])],
            ]);
            const fetchImpl = async (url) => {
              const bytes = files.get(url);
              return {
                ok: Boolean(bytes),
                status: bytes ? 200 : 404,
                headers: { get: (name) => name === "content-type" ? (url.endsWith(".ttf") ? "font/ttf" : "image/png") : "" },
                arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
              };
            };
            const result = await tools.buildUiKitPackage({
              name: "Rain UI Kit",
              gameUiConfig: {
                fontAssetId: "font_story",
                panelFrameAssetId: "ui_panel",
                buttonFrameAssetId: "ui_panel",
                accentColor: "#55aaff",
              },
              dialogBoxConfig: { panelAssetId: "ui_panel", textColor: "#ffffff" },
              assetList: [
                {
                  id: "ui_panel", type: "ui", name: "Rain Panel", path: "assets/ui/panel.png",
                  publicPath: "/panel.png", fileExists: true, tags: ["UI", "rain"],
                  license: "CC-BY-4.0", author: "Studio", attributionRequired: true,
                },
                {
                  id: "font_story", type: "font", name: "Story Font", path: "assets/fonts/story.ttf",
                  publicPath: "/story.ttf", fileExists: true, tags: ["font"], commercialUse: "可商用",
                },
              ],
            }, { fetchImpl, exportedAt: "2026-08-24T00:00:00.000Z" });
            const validation = await tools.validateUiKitPackage(result.bundle);
            const request = tools.buildUiKitImportRequest(validation);
            process.stdout.write(JSON.stringify({
              summary: validation.summary,
              integrity: result.bundle.integrity,
              roles: validation.bundle.assets.map((asset) => asset.roles),
              requestBindings: request.bindings,
              requestTypes: request.files.map((file) => file.assetType),
              displayNames: request.files.map((file) => file.displayName),
              panelRights: request.files.find((file) => file.assetType === "ui").rights,
              panelTags: request.files.find((file) => file.assetType === "ui").tags,
            }));
            """
        )

        self.assertEqual(payload["summary"]["assetCount"], 2)
        self.assertEqual(payload["summary"]["bindingCount"], 4)
        self.assertTrue(payload["integrity"].startswith("sha256:"))
        self.assertEqual(payload["requestTypes"], ["font", "ui"])
        self.assertEqual(payload["displayNames"], ["Story Font", "Rain Panel"])
        self.assertEqual(payload["requestBindings"]["gameUiConfig.panelFrameAssetId"], 1)
        self.assertEqual(payload["requestBindings"]["dialogBoxConfig.panelAssetId"], 1)
        self.assertIn("Canvasia UI Kit", payload["panelTags"])
        self.assertEqual(payload["panelRights"]["license"], "CC-BY-4.0")
        self.assertTrue(payload["panelRights"]["attributionRequired"])

    def test_validation_rejects_tampering_and_role_type_mismatch(self) -> None:
        payload = self.run_node(
            """
            const bytes = Buffer.from([137, 80, 78, 71, 1, 2, 3, 4]);
            const fetchImpl = async () => ({
              ok: true,
              status: 200,
              headers: { get: () => "image/png" },
              arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength),
            });
            const result = await tools.buildUiKitPackage({
              name: "Safe UI",
              gameUiConfig: { panelFrameAssetId: "ui_panel" },
              dialogBoxConfig: {},
              assetList: [{ id: "ui_panel", type: "ui", name: "Panel", path: "panel.png", publicPath: "/panel.png", fileExists: true }],
            }, { fetchImpl, exportedAt: "2026-08-24T00:00:00.000Z" });
            const tampered = JSON.parse(JSON.stringify(result.bundle));
            tampered.config.gameUiConfig.accentColor = "#ff0000";
            let integrityError = "";
            try { await tools.validateUiKitPackage(tampered); } catch (error) { integrityError = error.message; }

            const wrongType = JSON.parse(JSON.stringify(result.bundle));
            wrongType.assets[0].type = "background";
            wrongType.integrity = await tools.buildSha256Integrity(wrongType);
            let typeError = "";
            try { await tools.validateUiKitPackage(wrongType); } catch (error) { typeError = error.message; }

            const wrongRights = JSON.parse(JSON.stringify(result.bundle));
            wrongRights.assets[0].rights.attributionRequired = "false";
            wrongRights.integrity = await tools.buildSha256Integrity(wrongRights);
            let rightsError = "";
            try { await tools.validateUiKitPackage(wrongRights); } catch (error) { rightsError = error.message; }
            process.stdout.write(JSON.stringify({ integrityError, typeError, rightsError }));
            """
        )

        self.assertIn("完整性校验失败", payload["integrityError"])
        self.assertIn("类型与界面绑定不匹配", payload["typeError"])
        self.assertIn("授权布尔字段格式无效", payload["rightsError"])

    def test_injected_workflow_keeps_app_entrypoint_thin(self) -> None:
        payload = self.run_node(
            """
            const events = [];
            const packageApi = {
              UI_KIT_EXTENSION: ".canvasia-ui-kit.json",
              UI_KIT_MAX_FILE_BYTES: 1024,
              buildUiKitPackage: async (model) => ({
                bundle: { name: model.name },
                summary: { assetCount: 2, bindingCount: 3, totalBytes: 400 },
              }),
              validateUiKitPackage: async () => ({
                ok: true,
                bundle: { name: "Imported" },
                summary: { name: "Imported", assetCount: 1, bindingCount: 2, totalBytes: 300 },
              }),
              buildUiKitImportRequest: () => ({ request: "ready" }),
            };
            const workflow = tools.createUiKitWorkflow({
              packageApi,
              getProjectModel: () => ({ projectTitle: "Rain Story", assetList: [] }),
              getAssetUrl: () => "/asset",
              sanitizeFileName: (value) => value.toLowerCase().replaceAll(" ", "-"),
              downloadJsonFile: (name) => events.push(["download", name]),
              readFileAsText: async () => "{}",
              parseJsonImportText: () => ({}),
              formatFileSize: (value) => `${value} B`,
              confirmImport: async (model) => { events.push(["confirm", model.title]); return true; },
              postImport: async (request) => { events.push(["post", request.request]); return { importedCount: 1, bindingCount: 2 }; },
              reloadProjectData: async () => events.push(["reload"]),
              renderAll: () => events.push(["render"]),
              setSaveStatus: (message) => events.push(["status", message]),
              showToast: (message) => events.push(["toast", message]),
              showFailure: async (error) => events.push(["failure", error.message]),
            });
            const exported = await workflow.exportPackage();
            const imported = await workflow.importPackage({ size: 24 });
            process.stdout.write(JSON.stringify({ events, exported, imported }));
            """
        )

        self.assertEqual(payload["exported"]["summary"]["assetCount"], 2)
        self.assertEqual(payload["imported"]["importedCount"], 1)
        self.assertIn(["download", "rain-story.canvasia-ui-kit.json"], payload["events"])
        self.assertIn(["post", "ready"], payload["events"])
        self.assertIn(["reload"], payload["events"])
        self.assertIn(["render"], payload["events"])
        self.assertFalse(any(event[0] == "failure" for event in payload["events"]))


if __name__ == "__main__":
    unittest.main()
