from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "music_range_scope.js"


class FrontendMusicRangeScopeModuleTests(unittest.TestCase):
    def test_music_range_scope_helpers_run_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorMusicRangeScope;
            const scene = {{
              blocks: [
                {{ id: "bgm_a", type: "music_play", assetId: "theme", endMode: "after_block", endBlockId: "line_2" }},
                {{ id: "line_1", type: "dialogue", text: "第一句 & 起点" }},
                {{ id: "line_2", type: "narration", text: "终点 <safe>" }},
                {{ id: "stop", type: "music_stop" }},
              ],
            }};
            const emptyScene = {{ blocks: [{{ id: "bgm_only", type: "music_play", endMode: "after_block" }}] }};
            const helpers = {{
              getSafeMusicEndMode(mode) {{
                return ["until_next_music", "scene_end", "after_block"].includes(mode) ? mode : "until_next_music";
              }},
              getBlockLabel(type) {{
                return {{ music_play: "播放 BGM", dialogue: "台词", narration: "旁白", music_stop: "停止音乐" }}[type] || type;
              }},
              truncateText(value, maxLength) {{
                const text = String(value ?? "");
                return text.length > maxLength ? `${{text.slice(0, maxLength - 1)}}…` : text;
              }},
            }};
            const block = scene.blocks[0];
            const candidates = tools.getMusicRangeCandidateBlocks(scene, block).map((item) => item.id);
            const summary = tools.getMusicRangeSummary(scene, block, helpers);
            const timeline = tools.getMusicRangeTimeline(scene, block, helpers);
            const options = tools.renderMusicRangeEndBlockOptions(scene, block, helpers);
            const diagnostics = tools.buildMusicRangeDiagnostics(scene, block, helpers);
            const health = tools.renderMusicRangeHealthChips(diagnostics, helpers);
            const emptyDiagnostics = tools.buildMusicRangeDiagnostics(emptyScene, emptyScene.blocks[0], helpers);
            const backwardDiagnostics = tools.buildMusicRangeDiagnostics(
              scene,
              {{ id: "stop", type: "music_play", endMode: "after_block", endBlockId: "line_1" }},
              helpers
            );
            const sceneEndDiagnostics = tools.buildMusicRangeDiagnostics(
              scene,
              {{ id: "line_1", type: "music_play", endMode: "scene_end" }},
              helpers
            );
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              candidates,
              summary,
              timeline,
              options,
              diagnostics,
              health,
              emptyDiagnostics,
              backwardDiagnostics,
              sceneEndDiagnostics,
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

        self.assertIn("buildMusicRangeDiagnostics", payload["keys"])
        self.assertIn("renderMusicRangeEndBlockOptions", payload["keys"])
        self.assertEqual(payload["candidates"], ["line_1", "line_2", "stop"])
        self.assertIn("第 1 张播放到第 3 张", payload["summary"])
        self.assertIn("旁白", payload["summary"])
        self.assertEqual(payload["timeline"]["startLabel"], "第 1 张")
        self.assertEqual(payload["timeline"]["endLabel"], "第 3 张")
        self.assertEqual(payload["timeline"]["countLabel"], "覆盖 3 张")
        self.assertIn("终点 &lt;safe&gt;", payload["options"])
        self.assertEqual(payload["diagnostics"]["label"], "自定义范围有效")
        self.assertEqual(payload["diagnostics"]["spanCount"], 3)
        self.assertIn("覆盖 3 张", payload["health"])
        self.assertEqual(payload["emptyDiagnostics"]["label"], "还没有可选结束点")
        self.assertEqual(payload["emptyDiagnostics"]["tone"], "warn")
        self.assertEqual(payload["backwardDiagnostics"]["label"], "结束点早于播放点")
        self.assertEqual(payload["backwardDiagnostics"]["tone"], "danger")
        self.assertEqual(payload["sceneEndDiagnostics"]["label"], "覆盖到场景结束")


if __name__ == "__main__":
    unittest.main()
