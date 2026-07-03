from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "script_importer.js"


class FrontendScriptImporterModuleTests(unittest.TestCase):
    def test_script_importer_parses_plain_text_into_story_blocks(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorScriptImporter;
            const blocks = tools.parseScriptDraftToBlocks(`
              旁白：雨声贴着窗沿落下。
              悠奈：你终于来了。
              我把伞往她那边递过去。
              - 问她为什么在这里
              - 先沉默陪她一会儿
              1. 追上去
              2. 留在原地
              男主: 我知道了。
            `);
            const limited = tools.parseScriptDraftToBlocks("A：1\\nB：2\\nC：3", {{ maxBlocks: 2 }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              normalizedLines: tools.normalizeScriptImportText(" a\\r\\n\\n b ").join("|"),
              choiceLine: tools.parseChoiceLine("2. 追上去"),
              dialogueLine: tools.parseDialogueLine("悠奈：你终于来了。"),
              narrationLine: tools.parseDialogueLine("旁白：雨声变大了。"),
              blocks,
              summary: tools.summarizeScriptDraftBlocks(blocks),
              preview: tools.buildScriptDraftPreviewLines(blocks, 4),
              limitedCount: limited.length,
            }}));
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
        self.assertIn("parseScriptDraftToBlocks", payload["keys"])
        self.assertEqual(payload["normalizedLines"], "a|b")
        self.assertEqual(payload["choiceLine"], "追上去")
        self.assertEqual(payload["dialogueLine"], {
            "type": "dialogue",
            "speakerName": "悠奈",
            "text": "你终于来了。",
        })
        self.assertEqual(payload["narrationLine"], {"type": "narration", "text": "雨声变大了。"})
        self.assertEqual([block["type"] for block in payload["blocks"]], [
            "narration",
            "dialogue",
            "narration",
            "choice",
            "dialogue",
        ])
        self.assertEqual(payload["blocks"][3]["options"], [
            {"text": "问她为什么在这里"},
            {"text": "先沉默陪她一会儿"},
            {"text": "追上去"},
            {"text": "留在原地"},
        ])
        self.assertEqual(payload["summary"], {"dialogue": 2, "narration": 2, "choice": 1, "total": 5})
        self.assertIn("悠奈：你终于来了。", payload["preview"][1])
        self.assertEqual(payload["limitedCount"], 2)


if __name__ == "__main__":
    unittest.main()
