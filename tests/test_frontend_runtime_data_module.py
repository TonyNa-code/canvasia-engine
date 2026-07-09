from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_data.js"


class FrontendRuntimeDataModuleTests(unittest.TestCase):
    def test_runtime_data_normalizes_project_graph_and_endings(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const data = tools.normalizeGameData({{
              project: {{
                language: "zh-CN",
                chapterOrder: ["chapter_b", "chapter_a"],
              }},
              i18n: {{
                fallbackLanguage: "ja-JP",
                supportedLanguages: ["zh-CN", "en-US"],
                languageLabels: {{ "zh-CN": "简体中文" }},
              }},
              assets: {{ assets: [{{ id: "bg_school", type: "background" }}] }},
              characters: {{ characters: [{{ id: "heroine", name: "Heroine" }}] }},
              variables: {{ variables: [{{ id: "affection", type: "number" }}] }},
              chapters: [
                {{
                  chapterId: "chapter_a",
                  name: "A",
                  scenes: [
                    {{
                      id: "scene_a",
                      blocks: [
                        {{ type: "choice", options: [
                          {{ gotoSceneId: "__continue__" }},
                          {{ gotoSceneId: "scene_b" }},
                          {{ gotoSceneId: "scene_b" }}
                        ] }}
                      ],
                    }},
                  ],
                }},
                {{
                  chapterId: "chapter_b",
                  name: "B",
                  scenes: [
                    {{
                      id: "scene_b",
                      blocks: [
                        {{ type: "condition", branches: [{{ gotoSceneId: "scene_c" }}], elseGotoSceneId: "scene_d" }}
                      ],
                    }},
                    {{ id: "scene_c", blocks: [] }},
                    {{ id: "scene_d", blocks: [] }},
                  ],
                }},
              ],
              buildInfo: {{ copiedAssets: 1, missingAssets: [] }},
            }});

            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              chapterIds: data.chapters.map((chapter) => chapter.chapterId),
              sceneIds: data.scenes.map((scene) => scene.id),
              sceneAChapterName: data.scenesById.get("scene_a").chapterName,
              outgoingA: tools.collectSceneOutgoingTargets(data.scenesById.get("scene_a")),
              outgoingB: tools.collectSceneOutgoingTargets(data.scenesById.get("scene_b")),
              endings: data.endingScenes.map((scene) => scene.id),
              supportedLanguages: data.i18n.supportedLanguages,
              fallbackLanguage: data.i18n.fallbackLanguage,
              assetsByIdHasBg: data.assetsById.has("bg_school"),
              charactersByIdHasHeroine: data.charactersById.has("heroine"),
              variablesByIdHasAffection: data.variablesById.has("affection"),
              continueTarget: tools.CHOICE_CONTINUE_TARGET,
              isContinue: tools.isChoiceContinueTarget("__continue__"),
              isScene: tools.isChoiceContinueTarget("scene_a"),
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
        self.assertIn("normalizeGameData", payload["keys"])
        self.assertIn("collectSceneOutgoingTargets", payload["keys"])
        self.assertEqual(payload["chapterIds"], ["chapter_b", "chapter_a"])
        self.assertEqual(payload["sceneIds"], ["scene_b", "scene_c", "scene_d", "scene_a"])
        self.assertEqual(payload["sceneAChapterName"], "A")
        self.assertEqual(payload["outgoingA"], ["scene_b"])
        self.assertEqual(payload["outgoingB"], ["scene_c", "scene_d"])
        self.assertEqual(payload["endings"], ["scene_c", "scene_d"])
        self.assertEqual(payload["supportedLanguages"], ["zh-CN", "en-US"])
        self.assertEqual(payload["fallbackLanguage"], "ja-JP")
        self.assertTrue(payload["assetsByIdHasBg"])
        self.assertTrue(payload["charactersByIdHasHeroine"])
        self.assertTrue(payload["variablesByIdHasAffection"])
        self.assertEqual(payload["continueTarget"], "__continue__")
        self.assertTrue(payload["isContinue"])
        self.assertFalse(payload["isScene"])


if __name__ == "__main__":
    unittest.main()
