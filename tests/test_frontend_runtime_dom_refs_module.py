from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_dom_refs.js"
PLAYER_PATH = ROOT_DIR / "export_player_template" / "player.js"


class FrontendRuntimeDomRefsModuleTests(unittest.TestCase):
    def test_collects_id_refs_special_selectors_and_safe_fallbacks(self) -> None:
        script = textwrap.dedent(
            f"""
            import {{ createRuntimeDomRefs }} from {json.dumps(MODULE_PATH.as_uri())};

            const stageFrame = {{ id: "stageFrame" }};
            const systemMenu = {{ id: "systemMenu" }};
            const duplicate = {{ id: "systemMenu" }};
            const dialogPanel = {{ className: "dialog-panel" }};
            const themeButtons = [{{ id: "theme-auto" }}, {{ id: "theme-dark" }}];
            const documentRef = {{
              querySelector(selector) {{
                return selector === ".dialog-panel" ? dialogPanel : null;
              }},
              querySelectorAll(selector) {{
                if (selector === "[id]") return [stageFrame, systemMenu, duplicate, {{ id: "" }}];
                if (selector === ".player-theme-button") return themeButtons;
                return [];
              }},
            }};

            const refs = createRuntimeDomRefs(documentRef);
            const fallback = createRuntimeDomRefs(null);
            process.stdout.write(JSON.stringify({{
              stageFrame: refs.stageFrame === stageFrame,
              systemMenuUsesFirstId: refs.systemMenu === systemMenu,
              dialogPanel: refs.dialogPanel === dialogPanel,
              themeButtonCount: refs.runtimeThemeButtons.length,
              fallbackKeys: Object.keys(fallback).sort(),
              fallbackDialogPanel: fallback.dialogPanel,
              fallbackThemeButtonCount: fallback.runtimeThemeButtons.length,
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
        self.assertTrue(payload["stageFrame"])
        self.assertTrue(payload["systemMenuUsesFirstId"])
        self.assertTrue(payload["dialogPanel"])
        self.assertEqual(payload["themeButtonCount"], 2)
        self.assertEqual(payload["fallbackKeys"], ["dialogPanel", "runtimeThemeButtons"])
        self.assertIsNone(payload["fallbackDialogPanel"])
        self.assertEqual(payload["fallbackThemeButtonCount"], 0)

    def test_player_entrypoint_uses_the_dom_ref_module(self) -> None:
        player_source = PLAYER_PATH.read_text(encoding="utf-8")

        self.assertIn('from "./runtime_dom_refs.js"', player_source)
        self.assertIn("const refs = createRuntimeDomRefs(document);", player_source)
        self.assertNotIn("document.getElementById", player_source)


if __name__ == "__main__":
    unittest.main()
