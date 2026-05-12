from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_catalog.js"


class FrontendStoryBlockCatalogModuleTests(unittest.TestCase):
    def test_story_block_catalog_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStoryBlockCatalog;
            const result = {{
              keys: Object.keys(tools).sort(),
              labels: [
                tools.getBlockLabel("dialogue"),
                tools.getBlockLabel("particle_effect"),
                tools.getBlockLabel("custom_block"),
                tools.getBlockLabel(null),
              ],
              safeModes: [
                tools.getSafeMusicEndMode("scene_end"),
                tools.getSafeMusicEndMode("bad"),
                tools.getSafeMusicEndMode(null),
              ],
              musicLabels: [
                tools.getMusicEndModeLabel("after_block"),
                tools.getMusicEndModeLabel("bad"),
              ],
              optionMarkup: tools.renderMusicEndModeOptions("scene_end"),
              escapedMarkup: tools.renderMusicEndModeOptions("until_next_music", {{
                escapeHtml: (value) => String(value).replace(/播/g, "&#25773;"),
              }}),
              exportedLabels: tools.BLOCK_LABELS,
              exportedMusicLabels: tools.MUSIC_END_MODE_LABELS,
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
        self.assertIn("getBlockLabel", payload["keys"])
        self.assertIn("renderMusicEndModeOptions", payload["keys"])
        self.assertEqual(payload["labels"], ["台词", "粒子特效", "custom_block", "步骤"])
        self.assertEqual(payload["safeModes"], ["scene_end", "until_next_music", "until_next_music"])
        self.assertEqual(payload["musicLabels"], ["播到指定卡片后", "播到下一首或停止卡"])
        self.assertIn('<option value="scene_end" selected>', payload["optionMarkup"])
        self.assertIn('<option value="until_next_music" ', payload["optionMarkup"])
        self.assertIn("&#25773;到下一首或停止卡", payload["escapedMarkup"])
        self.assertEqual(payload["exportedLabels"]["video_play"], "播放视频")
        self.assertEqual(payload["exportedMusicLabels"]["after_block"], "播到指定卡片后")


if __name__ == "__main__":
    unittest.main()
