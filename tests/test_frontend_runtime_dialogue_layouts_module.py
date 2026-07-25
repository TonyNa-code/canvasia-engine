from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_dialogue_layouts.js"


class FrontendRuntimeDialogueLayoutsModuleTests(unittest.TestCase):
    def test_dialogue_layout_rules_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            (async () => {{
              const module = await import({json.dumps(MODULE_PATH.as_uri())});
              const blocks = [
                {{ id: "adv", type: "dialogue", text: "经典", dialogueLayout: "adv" }},
                {{ id: "nvl_1", type: "narration", text: "第一句", dialogueLayout: "nvl", nvlPageBreak: true }},
                {{ id: "effect", type: "screen_shake" }},
                {{ id: "nvl_2", type: "dialogue", speakerId: "hero", text: "第二句", dialogueLayout: "nvl" }},
                {{ id: "nvl_3", type: "narration", text: "第三句", dialogueLayout: "nvl" }},
                {{ id: "choice", type: "choice" }},
                {{ id: "nvl_4", type: "narration", text: "新段", dialogueLayout: "nvl" }},
              ];
              const entries = module.collectNvlPageEntries(blocks, 4, {{
                resolveEntry: (block, index) => ({{
                  id: block.id,
                  blockIndex: index,
                  type: block.type,
                  speakerName: block.speakerId === "hero" ? "主人公" : "",
                  text: block.text,
                }}),
              }});
              const afterChoice = module.collectNvlPageEntries(blocks, 6);
              const presentation = module.buildDialogueLayoutPresentation(blocks[4], {{
                blocks,
                currentIndex: 4,
              }});
              process.stdout.write(JSON.stringify({{
                ids: module.DIALOGUE_LAYOUT_IDS,
                labels: module.DIALOGUE_LAYOUT_LABELS,
                fallback: module.getSafeDialogueLayout("unknown"),
                nonTextLayout: module.getDialogueLayoutFromBlock({{ type: "choice", dialogueLayout: "nvl" }}),
                startsPage: module.shouldStartNewNvlPage(blocks[1]),
                entries,
                afterChoice,
                presentation,
                globalAttached: globalThis.CanvasiaRuntimeDialogueLayouts === module.default
                  || globalThis.CanvasiaRuntimeDialogueLayouts?.getSafeDialogueLayout === module.getSafeDialogueLayout,
              }}));
            }})().catch((error) => {{
              console.error(error);
              process.exit(1);
            }});
            """
        )
        result = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(payload["ids"], ["adv", "nvl", "cinematic"])
        self.assertEqual(payload["fallback"], "adv")
        self.assertEqual(payload["nonTextLayout"], "adv")
        self.assertTrue(payload["startsPage"])
        self.assertTrue(payload["globalAttached"])
        self.assertEqual([entry["id"] for entry in payload["entries"]], ["nvl_1", "nvl_2", "nvl_3"])
        self.assertEqual(payload["entries"][1]["speakerName"], "主人公")
        self.assertEqual([entry["id"] for entry in payload["afterChoice"]], ["nvl_4"])
        self.assertEqual(payload["presentation"]["layout"], "nvl")
        self.assertEqual(len(payload["presentation"]["entries"]), 3)
        self.assertIn("NVL", payload["labels"]["nvl"])


if __name__ == "__main__":
    unittest.main()
