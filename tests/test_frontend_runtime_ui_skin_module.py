from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_ui_skin.js"
EDITOR_SETTINGS_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_settings.js"


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


class FrontendRuntimeUiSkinModuleTests(unittest.TestCase):
    def test_runtime_normalizes_ui_and_dialog_configuration(self) -> None:
        payload = run_node_module(
            """
            const project = {
              dialogBoxConfig: {
                preset: "custom",
                shape: "triangle",
                widthPercent: 10,
                minHeight: 999,
                backgroundColor: "not-a-color",
                panelAssetFit: "stretch",
                anchor: "free",
                offsetXPercent: -99,
              },
              gameUiConfig: {
                preset: "custom",
                layoutPreset: "broken",
                fontFamily: "Source Han Serif SC; url(evil)",
                fontAssetId: "font-main",
                sidePanelWidth: 999,
                panelOpacity: -1,
                panelFrameSlice: { top: -9, right: 120, bottom: 12, left: 18 },
              },
            };
            const dialog = tools.getProjectDialogBoxConfig(project);
            const gameUi = tools.getProjectGameUiConfig(project);
            const presentation = tools.buildDialogBoxPresentation("project", {
              ...project,
              dialogBoxConfig: { ...project.dialogBoxConfig, panelAssetId: "panel" },
            }, {
              getAssetUrl: (id) => `assets/${id}\"\n.png`,
            });
            const softenedPresentation = tools.buildDialogBoxPresentation("project", {
              dialogBoxConfig: {
                preset: "custom",
                backgroundColor: "#102030",
                backgroundOpacity: 80,
                borderColor: "#405060",
                borderOpacity: 40,
                panelAssetId: "panel",
                panelAssetOpacity: 60,
              },
            }, {
              getAssetUrl: (id) => `assets/${id}.png`,
              dialogBoxOpacityPercent: 50,
            });
            process.stdout.write(JSON.stringify({
              dialog,
              gameUi,
              rgba: tools.toRgbaString("#102030", 25),
              presentation,
              softenedPresentation,
            }));
            """
        )

        self.assertEqual(payload["dialog"]["shape"], "rounded")
        self.assertEqual(payload["dialog"]["widthPercent"], 55)
        self.assertEqual(payload["dialog"]["minHeight"], 320)
        self.assertEqual(payload["dialog"]["panelAssetFit"], "cover")
        self.assertEqual(payload["dialog"]["anchor"], "free")
        self.assertEqual(payload["dialog"]["offsetXPercent"], -35)
        self.assertEqual(payload["gameUi"]["layoutPreset"], "balanced")
        self.assertEqual(payload["gameUi"]["fontAssetId"], "font-main")
        self.assertNotIn(";", payload["gameUi"]["fontFamily"])
        self.assertNotIn("(", payload["gameUi"]["fontFamily"])
        self.assertEqual(payload["gameUi"]["sidePanelWidth"], 460)
        self.assertEqual(payload["gameUi"]["panelOpacity"], 35)
        self.assertEqual(payload["gameUi"]["panelFrameSlice"], {"top": 0, "right": 96, "bottom": 12, "left": 18})
        self.assertEqual(payload["rgba"], "rgba(16, 32, 48, 0.25)")
        self.assertNotIn("\n", payload["presentation"]["style"])
        self.assertIn("%22", payload["presentation"]["style"])
        self.assertIn("rgba(16, 32, 48, 0.40)", payload["softenedPresentation"]["style"])
        self.assertIn("rgba(64, 80, 96, 0.20)", payload["softenedPresentation"]["style"])
        self.assertIn("--dialog-box-art-opacity: 0.30", payload["softenedPresentation"]["style"])

    def test_editor_and_runtime_share_the_same_safe_ui_configuration(self) -> None:
        script = textwrap.dedent(
            f"""
            globalThis.window = globalThis;
            await import({json.dumps(EDITOR_SETTINGS_PATH.as_uri())});
            const runtime = await import({json.dumps(MODULE_PATH.as_uri())});
            const editor = globalThis.CanvasiaEditorProjectSettings;
            const project = {{
              dialogBoxConfig: {{
                preset: "custom",
                shape: "capsule",
                widthPercent: 77,
                panelAssetId: "dialog-frame",
                offsetYPercent: 8,
              }},
              gameUiConfig: {{
                preset: "custom",
                layoutPreset: "compact",
                fontStyle: "serif",
                fontFamily: "Source Han Serif SC",
                fontAssetId: "font-main",
                layoutGap: 19,
                panelOpacity: 73,
                buttonFrameSlice: {{ top: 3, right: 4, bottom: 5, left: 6 }},
              }},
            }};
            process.stdout.write(JSON.stringify({{
              dialogEditor: editor.getProjectDialogBoxConfig(project),
              dialogRuntime: runtime.getProjectDialogBoxConfig(project),
              gameUiEditor: editor.getProjectGameUiConfig(project),
              gameUiRuntime: runtime.getProjectGameUiConfig(project),
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
        self.assertEqual(payload["dialogEditor"], payload["dialogRuntime"])
        self.assertEqual(payload["gameUiEditor"], payload["gameUiRuntime"])

    def test_skin_applies_css_branding_and_custom_font_with_safe_fallback(self) -> None:
        payload = run_node_module(
            """
            const createDocument = () => {
              const values = {};
              const nodes = {
                ".player-brand-copy .eyebrow": { textContent: "" },
                ".start-card > .eyebrow": { textContent: "" },
                ".start-brand-copy strong": { textContent: "" },
                ".start-brand-copy span": { textContent: "" },
              };
              const images = [{ src: "" }, { src: "" }];
              const addedFonts = [];
              return {
                values,
                nodes,
                images,
                addedFonts,
                documentRef: {
                  documentElement: {
                    dataset: {},
                    style: {
                      setProperty(name, value) { values[name] = value; },
                      removeProperty(name) { delete values[name]; },
                    },
                  },
                  fonts: { add(font) { addedFonts.push(font); } },
                  querySelector(selector) { return nodes[selector] ?? null; },
                  querySelectorAll() { return images; },
                },
              };
            };

            class WorkingFontFace {
              constructor(family, source) { this.family = family; this.source = source; }
              async load() { return this; }
            }
            class BrokenFontFace {
              async load() { throw new Error("font decode failed"); }
            }

            const loaded = createDocument();
            const loadedResult = tools.applyProjectGameUiSkin({
              title: "Project Aurora",
              gameUiConfig: {
                preset: "custom",
                brandMode: "project",
                fontFamily: "Source Han Serif SC",
                fontAssetId: "font-main",
                titleLogoAssetId: "logo-main",
                accentColor: "#123456",
              },
            }, {
              documentRef: loaded.documentRef,
              FontFaceCtor: WorkingFontFace,
              getAssetUrl: (id) => `assets/${id}.woff2`,
            });
            const loadedFont = await loadedResult.fontPromise;

            const fallback = createDocument();
            const fallbackResult = tools.applyProjectGameUiSkin({
              gameUiConfig: {
                preset: "custom",
                fontFamily: "Noto Sans CJK SC",
                fontAssetId: "broken-font",
              },
            }, {
              documentRef: fallback.documentRef,
              FontFaceCtor: BrokenFontFace,
              getAssetUrl: (id) => `assets/${id}.woff2`,
            });
            const fallbackFont = await fallbackResult.fontPromise;

            process.stdout.write(JSON.stringify({
              loaded: {
                applied: loadedResult.applied,
                font: loadedFont,
                dataset: loaded.documentRef.documentElement.dataset,
                values: loaded.values,
                fontCount: loaded.addedFonts.length,
                fontSource: loaded.addedFonts[0]?.source,
                topBrand: loaded.nodes[".player-brand-copy .eyebrow"].textContent,
                startTitle: loaded.nodes[".start-brand-copy strong"].textContent,
                logoSources: loaded.images.map((image) => image.src),
              },
              fallback: {
                font: fallbackFont,
                dataset: fallback.documentRef.documentElement.dataset,
                values: fallback.values,
              },
            }));
            """
        )

        self.assertTrue(payload["loaded"]["applied"])
        self.assertEqual(payload["loaded"]["font"]["status"], "loaded")
        self.assertEqual(payload["loaded"]["fontCount"], 1)
        self.assertIn("font-main.woff2", payload["loaded"]["fontSource"])
        self.assertEqual(payload["loaded"]["dataset"]["gameUiCustomFont"], "loaded")
        self.assertEqual(payload["loaded"]["values"]["--game-ui-accent"], "#123456")
        self.assertIn("CanvasiaProjectFont", payload["loaded"]["values"]["--game-ui-font-family"])
        self.assertEqual(payload["loaded"]["topBrand"], "Project Aurora · Runtime")
        self.assertEqual(payload["loaded"]["startTitle"], "Project Aurora")
        self.assertEqual(payload["loaded"]["logoSources"], ["assets/logo-main.woff2", "assets/logo-main.woff2"])

        self.assertEqual(payload["fallback"]["font"]["status"], "fallback")
        self.assertEqual(payload["fallback"]["dataset"]["gameUiCustomFont"], "fallback")
        self.assertEqual(payload["fallback"]["values"]["--game-ui-font-family"], "Noto Sans CJK SC")

    def test_late_custom_font_cannot_override_a_newer_system_font_choice(self) -> None:
        payload = run_node_module(
            """
            const values = {};
            const root = {
              dataset: {},
              style: {
                setProperty(name, value) { values[name] = value; },
                removeProperty(name) { delete values[name]; },
              },
            };
            const documentRef = {
              documentElement: root,
              fonts: { add() {} },
            };
            let releaseFont;
            const pendingFont = new Promise((resolve) => { releaseFont = resolve; });
            class DeferredFontFace {
              constructor(family) { this.family = family; }
              load() { return pendingFont.then(() => this); }
            }

            const first = tools.applyProjectGameUiFont({
              fontFamily: "Noto Serif CJK SC",
              fontAssetId: "slow-font",
            }, {
              documentRef,
              FontFaceCtor: DeferredFontFace,
              getAssetUrl: () => "assets/slow-font.woff2",
            });
            const second = await tools.applyProjectGameUiFont({
              fontFamily: "Noto Sans CJK SC",
              fontAssetId: "",
            }, { documentRef });
            releaseFont();
            const firstResult = await first;

            process.stdout.write(JSON.stringify({
              first: firstResult,
              second,
              dataset: root.dataset,
              values,
            }));
            """
        )

        self.assertEqual(payload["first"]["status"], "stale")
        self.assertEqual(payload["second"]["status"], "system")
        self.assertEqual(payload["dataset"]["gameUiCustomFont"], "system")
        self.assertEqual(payload["values"]["--game-ui-font-family"], "Noto Sans CJK SC")


if __name__ == "__main__":
    unittest.main()
