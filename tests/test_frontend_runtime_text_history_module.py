from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_text_history.js"


class FrontendRuntimeTextHistoryModuleTests(unittest.TestCase):
    def run_module_script(self, body: str) -> dict:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};
            {body}
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
        return json.loads(completed.stdout)

    def test_history_view_searches_full_timeline_and_preserves_absolute_indices(self) -> None:
        payload = self.run_module_script(
            """
            const session = {
              position: 2,
              timeline: [
                { sceneName: "教室", blockType: "dialogue", visualState: { speakerName: "Alice", dialogueText: "早上好" } },
                { sceneName: "教室", blockType: "narration", visualState: { speakerName: "旁白", dialogueText: "风吹过窗边" } },
                { sceneName: "屋顶", blockType: "dialogue", voice: "voice-1", visualState: { speakerName: "Bob", dialogueText: "一起回家吧" } },
                { sceneName: "屋顶", blockType: "dialogue", visualState: { speakerName: "Alice", dialogueText: `${"很长的铺垫".repeat(30)}终点关键词` } },
              ],
            };
            const options = {
              getBlockLabel: (value) => value === "dialogue" ? "台词" : "旁白",
              getVoiceAssetId: (snapshot) => snapshot.voice || "",
              stripStoryText: (value) => String(value || ""),
            };
            const all = tools.buildRuntimeHistoryView(session, {}, options);
            const sceneSearch = tools.buildRuntimeHistoryView(session, { query: "屋顶" }, options);
            const voiceSearch = tools.buildRuntimeHistoryView(session, { voicedOnly: true }, options);
            const speakerSearch = tools.buildRuntimeHistoryView(session, { speaker: "Alice" }, options);
            const longTextSearch = tools.buildRuntimeHistoryView(session, { query: "终点关键词" }, options);
            process.stdout.write(JSON.stringify({
              normalized: tools.normalizeRuntimeHistoryQuery(" ＡＢＣ "),
              speakers: all.speakers,
              sceneIndices: sceneSearch.visibleRecords.map((item) => item.index),
              voiceIndices: voiceSearch.visibleRecords.map((item) => item.index),
              speakerIndices: speakerSearch.visibleRecords.map((item) => item.index),
              longTextIndices: longTextSearch.visibleRecords.map((item) => item.index),
              previous: tools.getRuntimeHistoryStepIndex(session, -1),
              outOfRange: tools.getRuntimeHistoryStepIndex(session, 2),
            }));
            """
        )

        self.assertEqual(payload["normalized"], "abc")
        self.assertEqual(payload["speakers"], ["Alice", "旁白", "Bob"])
        self.assertEqual(payload["sceneIndices"], [2, 3])
        self.assertEqual(payload["voiceIndices"], [2])
        self.assertEqual(payload["speakerIndices"], [0, 3])
        self.assertEqual(payload["longTextIndices"], [3])
        self.assertEqual(payload["previous"], 1)
        self.assertIsNone(payload["outOfRange"])

    def test_controller_renders_safe_toolbar_and_updates_filters(self) -> None:
        payload = self.run_module_script(
            """
            const escapeHtml = (value) => String(value ?? "")
              .replaceAll("&", "&amp;")
              .replaceAll("<", "&lt;")
              .replaceAll(">", "&gt;")
              .replaceAll('"', "&quot;");
            const controller = tools.createRuntimeHistoryController({
              escapeHtml,
              renderEmpty: (value) => `<em>${escapeHtml(value)}</em>`,
              getBlockLabel: () => "台词",
              getVoiceAssetId: (snapshot) => snapshot.voice,
              stripStoryText: (value) => value,
            });
            const target = (selector, value = "") => ({
              value,
              matches: (candidate) => candidate === selector,
            });
            controller.updateFromTarget(target("[data-history-search]", "秘密"));
            controller.updateFromTarget(target("[data-history-speaker]", "<Alice>"));
            controller.updateFromTarget(target("[data-history-voiced]"));
            const session = {
              position: 0,
              timeline: [{
                sceneName: "秘密基地",
                blockType: "dialogue",
                voice: "voice-1",
                visualState: { speakerName: "<Alice>", dialogueText: "不要告诉别人" },
              }],
            };
            const html = controller.render(session);
            const activeFilters = controller.getFilters();
            controller.updateFromTarget(target("[data-history-clear]"));
            process.stdout.write(JSON.stringify({
              activeFilters,
              clearedFilters: controller.getFilters(),
              hasToolbar: html.includes('class="history-toolbar"'),
              hasResult: html.includes("找到 1 / 1 条"),
              escapedSpeaker: html.includes("&lt;Alice&gt;"),
              selected: html.includes("history-row is-selected"),
            }));
            """
        )

        self.assertEqual(
            payload["activeFilters"],
            {"query": "秘密", "speaker": "<Alice>", "voicedOnly": True},
        )
        self.assertEqual(
            payload["clearedFilters"],
            {"query": "", "speaker": "", "voicedOnly": False},
        )
        self.assertTrue(payload["hasToolbar"])
        self.assertTrue(payload["hasResult"])
        self.assertTrue(payload["escapedSpeaker"])
        self.assertTrue(payload["selected"])


if __name__ == "__main__":
    unittest.main()
