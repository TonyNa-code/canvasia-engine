from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_character_cards.js"


class FrontendRuntimeCharacterCardsModuleTests(unittest.TestCase):
    def test_shared_character_card_builder_handles_focus_motion_and_leaving_copy(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};
            const model = {{
              visibleCharacters: [
                {{ characterId: "hero", position: "left", stage: {{ offsetX: 2 }} }},
                {{ characterId: "heroine", position: "right" }},
              ],
              depthBlur: {{ focus: "left", strength: "medium" }},
              characterTransitionEvent: {{
                mode: "hide",
                transition: "fade",
                durationMs: 480,
                characterState: {{ characterId: "heroine", position: "right" }},
              }},
              activeCharacterId: "hero",
              characterEmphasisEvent: {{ characterId: "hero" }},
              visualComfortMode: "standard",
              gameUiConfig: {{ speakerFocusMode: "soft", speakerFocusIntensity: 65 }},
            }};
            const cards = tools.collectRenderableCharacterCards(model.visibleCharacters, model.characterTransitionEvent);
            const presentations = [];
            const html = tools.renderCharacterCards(model, {{
              getPositionOrder: (position) => ({{ left: 0, center: 1, right: 2 }}[position] ?? 1),
              getSafeTransition: (value) => value || "none",
              getSafeTransitionDurationMs: (value) => Number(value ?? 360),
              scaleVisualTransitionMs: (value) => value,
              getCharacterStageStyle: () => "--sprite-stage-scale:1;",
              getCharacterMotionStyle: () => "",
              shouldBlurCharacter: (position, depthBlur) => depthBlur?.focus !== "full" && position !== depthBlur?.focus,
              getSafeDepthBlurStrength: (value) => value || "medium",
              renderCard: (character, presentation) => {{
                presentations.push({{ characterId: character.characterId, ghost: Boolean(character.__ghostMode), ...presentation }});
                return `<i>${{character.characterId}}:${{presentation.transition}}</i>`;
              }},
            }});
            process.stdout.write(JSON.stringify({{
              cardCount: cards.length,
              html,
              presentations: presentations.map((item) => ({{
                characterId: item.characterId,
                ghost: item.ghost,
                classes: item.classes,
                role: item.speakerFocusPresentation.role,
                stageStyle: item.stageStyle,
              }})),
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

        self.assertEqual(payload["cardCount"], 3)
        self.assertEqual(payload["html"].count("<i>"), 3)
        hero = next(item for item in payload["presentations"] if item["characterId"] == "hero")
        ghost = next(item for item in payload["presentations"] if item["ghost"])
        self.assertIn("is-speaking", hero["classes"])
        self.assertIn("is-emphasis", hero["classes"])
        self.assertEqual(hero["role"], "active")
        self.assertIn("--sprite-transition-ms:480ms", hero["stageStyle"])
        self.assertIn("is-leaving", ghost["classes"])


if __name__ == "__main__":
    unittest.main()
