from __future__ import annotations

import json
import re
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_DIR = ROOT_DIR / "prototype_editor"
APP_PATH = EDITOR_DIR / "app.js"
CATALOG_MODULE_PATH = EDITOR_DIR / "modules" / "story_block_catalog.js"


def _extract_function_source(source: str, function_name: str) -> str:
    marker_match = re.search(
        rf"(?:async\s+)?function\s+{re.escape(function_name)}\s*\(",
        source,
    )
    if not marker_match:
        raise AssertionError(f"Missing function {function_name}")
    signature_depth = 0
    body_start = -1
    for index in range(marker_match.end() - 1, len(source)):
        char = source[index]
        if char == "(":
            signature_depth += 1
        elif char == ")":
            signature_depth -= 1
            if signature_depth == 0:
                body_start = source.find("{", index)
                break
    if body_start < 0:
        raise AssertionError(f"Missing function body for {function_name}")

    depth = 0
    for index in range(body_start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[body_start : index + 1]
    raise AssertionError(f"Unclosed function body for {function_name}")


def _load_story_block_catalog_payload() -> dict:
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        const vm = require("vm");
        const context = {{ window: {{}} }};
        context.globalThis = context;
        vm.createContext(context);
        vm.runInContext(fs.readFileSync({json.dumps(str(CATALOG_MODULE_PATH))}, "utf8"), context);
        const tools = context.window.CanvasiaEditorStoryBlockCatalog;
        process.stdout.write(JSON.stringify({{
          knownTypes: tools.getKnownBlockTypes(),
          labelTypes: Object.keys(tools.BLOCK_LABELS),
          runtimeTypes: tools.getRuntimeCapabilityRows().map((row) => row.type),
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
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


class FrontendStoryBlockRegistryIntegrationTests(unittest.TestCase):
    def test_registered_story_blocks_have_editor_entrypoints_and_runtime_rows(self) -> None:
        payload = _load_story_block_catalog_payload()
        source = APP_PATH.read_text(encoding="utf-8")
        handle_click = _extract_function_source(source, "handleClick")
        add_block = _extract_function_source(source, "addBlock")
        create_default_block = _extract_function_source(source, "createDefaultBlock")

        known_types = set(payload["knownTypes"])
        label_types = set(payload["labelTypes"])
        runtime_types = set(payload["runtimeTypes"])
        created_types = set(re.findall(r'\bif\s*\(\s*blockType\s*===\s*"([^"]+)"\s*\)', create_default_block))
        add_action_types = set(re.findall(r'\baddBlock\("([^"]+)"\)', handle_click))

        self.assertGreaterEqual(len(known_types), 20)
        self.assertEqual(known_types, label_types)
        self.assertEqual(known_types, runtime_types)
        self.assertEqual(known_types, created_types)
        self.assertEqual(known_types, add_action_types)
        self.assertIn("isKnownStoryBlockType(safeBlockType)", add_block)
        self.assertIn("未知剧情卡片类型", add_block)


if __name__ == "__main__":
    unittest.main()
