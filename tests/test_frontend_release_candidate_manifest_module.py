from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "release_candidate_manifest.js"


class FrontendReleaseCandidateManifestModuleTests(unittest.TestCase):
    def test_release_candidate_manifest_builds_handoff_bundle(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorReleaseCandidateManifest;
            const data = {{
              project: {{
                title: "RC Demo",
                language: "zh-CN",
                supportedLanguages: ["zh-CN", "en-US"],
                resolution: {{ width: 1920, height: 1080 }},
              }},
              assetList: [
                {{ id: "bg_room", type: "background", name: "Classroom", fileExists: true, fileSizeBytes: 2048 }},
                {{ id: "voice_001", type: "voice", name: "Voice 001", fileExists: true, fileSizeBytes: 1024 }},
                {{ id: "tmp", type: "image", name: "placeholder sprite", fileExists: true, tags: ["placeholder"] }},
              ],
              characters: [{{ id: "hero", name: "Hero" }}],
              chapters: [
                {{
                  chapterId: "chapter_1",
                  name: "Chapter 1",
                  scenes: [
                    {{
                      id: "scene_start",
                      name: "Start",
                      blocks: [
                        {{ id: "bg", type: "background", assetId: "bg_room" }},
                        {{ id: "music", type: "music_play", assetId: "bgm_main" }},
                        {{ id: "show", type: "character_show", characterId: "hero" }},
                        {{ id: "line", type: "dialogue", speakerId: "hero", text: "Hello.", voiceAssetId: "voice_001" }},
                        {{ id: "choice", type: "choice", options: [{{ text: "Go", targetSceneId: "scene_end" }}] }},
                      ],
                    }},
                    {{
                      id: "scene_end",
                      name: "Ending",
                      blocks: [
                        {{ id: "n", type: "narration", text: "The end." }},
                        {{ id: "credits", type: "credits_roll", title: "Staff" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const manifest = tools.buildReleaseCandidateManifest({{
              data,
              releaseVersion: "1.2.0-rc1",
              editorMode: "advanced",
              editorModeLabel: "Advanced",
              routeOverview: {{ metrics: {{ endingScenes: 1 }} }},
              validation: {{ errorCount: 0, warningCount: 1 }},
              releaseChecklistItems: [
                {{ severity: "warn", title: "Preview regression not run", description: "Run one smoke pass.", status: "待确认" }},
                {{ severity: "good", title: "Version set", description: "Version is ready." }},
              ],
              productionBacklog: {{
                summary: {{ taskCount: 2, blockerCount: 1, warningCount: 1, readinessPercent: 68 }},
                tasks: [
                  {{ severity: "blocker", areaLabel: "Assets", title: "Missing BGM", source: "Start", detail: "Bind bgm_main.", action: {{ label: "Go assets" }} }},
                ],
              }},
              runtimeCapabilityMatrix: {{
                summary: {{ totalBlockCount: 7, usedTypeCount: 6, issueCount: 1, partialUsedTypeCount: 1, unknownUsedTypeCount: 0, unsupportedUsedTypeCount: 0 }},
                acceptance: {{ summary: {{ itemCount: 4 }} }},
                issues: [{{ severity: "warn", title: "video_play needs review", detail: "Native video fallback.", sceneNames: ["OP"] }}],
              }},
              localizationCoverage: {{
                summary: {{ supportedLanguageCount: 2, readyPercent: 75, missingCount: 3 }},
                supportedLanguages: ["zh-CN", "en-US"],
                issues: [{{ severity: "warn", title: "Missing translation", detail: "English line missing.", languageLabel: "English" }}],
              }},
              unlockableContentManifest: {{
                summary: {{
                  totalEntryCount: 12,
                  readyEntryCount: 9,
                  missingEntryCount: 3,
                  achievementCount: 4,
                  endingCount: 2,
                  reachableEndingCount: 1,
                  readinessPercent: 75,
                  warningCount: 2,
                }},
                issues: [
                  {{ severity: "warn", groupId: "extra_cg", title: "CG 文件缺失", detail: "回忆 CG 没有可用文件。" }},
                  {{ severity: "warn", groupId: "ending_collection", title: "结局当前不可达", detail: "Hidden Ending 暂时无法抵达。" }},
                ],
              }},
              screenplay: {{ summary: {{ lineCount: 2, choiceCount: 1 }} }},
              directorCueSheet: {{
                summary: {{ sceneCount: 2, cueCount: 7, issueCount: 1, blockerCount: 1, warningCount: 0 }},
                issues: [{{ severity: "blocker", title: "Scene lacks background", detail: "Add a background.", chapterName: "Chapter 1", sceneName: "Ending" }}],
              }},
              voiceSheet: {{ summary: {{ lineCount: 1, readyLineCount: 1, missingVoiceCount: 0, missingFileCount: 0, missingAssetCount: 0 }} }},
              exportResult: {{
                target: "native_runtime",
                targetLabel: "Native Runtime",
                buildPath: "dist/RC Demo",
                missingAssets: 0,
                archiveSha256: "abc123",
                archiveSizeLabel: "12 MB",
                archivePublicUrl: "/exports/rc.zip",
              }},
              regressionResult: {{ summary: {{ passCount: 1, failCount: 0 }} }},
            }});
            const digest = tools.getReleaseCandidateStatusDigest(manifest);
            const markdown = tools.buildReleaseCandidateMarkdown(manifest, {{
              projectTitle: "RC Demo",
              generatedAt: "2026-07-05 13:00:00",
            }});
            const csv = tools.buildReleaseCandidateCsv(manifest);
            const panel = tools.renderReleaseCandidateManifestPanel(manifest);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              manifest,
              digest,
              markdown,
              csv,
              panel,
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
        manifest = payload["manifest"]
        self.assertIn("buildReleaseCandidateManifest", payload["keys"])
        self.assertIn("buildReleaseCandidateMarkdown", payload["keys"])
        self.assertIn("buildReleaseCandidateCsv", payload["keys"])
        self.assertIn("renderReleaseCandidateManifestPanel", payload["keys"])
        self.assertEqual(manifest["project"]["title"], "RC Demo")
        self.assertEqual(manifest["project"]["releaseVersion"], "1.2.0-rc1")
        self.assertEqual(manifest["content"]["sceneCount"], 2)
        self.assertEqual(manifest["content"]["blockCount"], 7)
        self.assertEqual(manifest["content"]["languageCount"], 2)
        self.assertEqual(manifest["assets"]["placeholderCount"], 1)
        self.assertEqual(len(manifest["deliverables"]), 10)
        self.assertEqual(manifest["status"], "blocked")
        self.assertEqual(payload["digest"]["status"], "blocked")
        self.assertEqual(manifest["unlockables"]["totalEntryCount"], 12)
        self.assertEqual(manifest["unlockables"]["readyEntryCount"], 9)
        self.assertEqual(manifest["unlockables"]["reachableEndingCount"], 1)
        self.assertTrue(any(item["id"] == "playable_export" and item["status"] == "ready" for item in manifest["deliverables"]))
        self.assertTrue(any(item["id"] == "localization_pack" and item["status"] == "review" for item in manifest["deliverables"]))
        self.assertTrue(any(item["id"] == "unlockable_manifest" and item["status"] == "review" for item in manifest["deliverables"]))
        self.assertTrue(any(risk["area"] == "Assets" and risk["title"] == "Missing BGM" for risk in manifest["risks"]))
        self.assertTrue(any(risk["area"] == "Director cues" for risk in manifest["risks"]))
        self.assertTrue(any(risk["area"] == "Unlockables" and risk["title"] == "结局当前不可达" for risk in manifest["risks"]))
        self.assertTrue(any(item["id"] == "save_load" and item["required"] for item in manifest["signoffChecklist"]))
        self.assertTrue(any(item["id"] == "audio_mix" and item["required"] for item in manifest["signoffChecklist"]))
        self.assertTrue(any(item["id"] == "extras_unlockables" and item["required"] for item in manifest["signoffChecklist"]))
        self.assertIn("# RC Demo Release Candidate Manifest", payload["markdown"])
        self.assertIn("## Manual Signoff", payload["markdown"])
        self.assertIn("9/12", payload["markdown"])
        self.assertIn("Playable build", payload["markdown"])
        self.assertIn("Unlockable content manifest", payload["markdown"])
        self.assertIn('"deliverable"', payload["csv"])
        self.assertIn('"signoff"', payload["csv"])
        self.assertIn('data-action="export-release-candidate-manifest-markdown"', payload["panel"])
        self.assertIn("Manual signoff checklist", payload["panel"])


if __name__ == "__main__":
    unittest.main()
