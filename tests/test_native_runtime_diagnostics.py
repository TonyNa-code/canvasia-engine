from __future__ import annotations

import unittest

from native_runtime.runtime_diagnostics import build_runtime_diagnostics_report


class NativeRuntimeDiagnosticsTests(unittest.TestCase):
    def test_runtime_diagnostics_report_summarizes_preload_prefetch_and_cache_state(self) -> None:
        report = build_runtime_diagnostics_report(
            {
                "sceneId": "scene_opening",
                "sceneName": "Opening",
                "blockIndex": 2,
                "lineType": "台词",
                "choiceCount": 1,
                "statusMessage": "当前卡片：台词",
                "runtimePreloadStatus": {
                    "status": "warming",
                    "totalEntries": 5,
                    "loadedEntries": 3,
                    "pendingEntries": 2,
                    "imageEntries": 3,
                    "loadedImageEntries": 2,
                    "soundEntries": 1,
                    "loadedSoundEntries": 1,
                    "streamEntries": 1,
                    "readyStreamEntries": 0,
                    "missingEntries": 0,
                    "failedEntries": 0,
                    "audioUnavailableEntries": 0,
                    "totalBytes": 4096,
                    "criticalBytes": 2048,
                    "loadedBytes": 2048,
                },
                "runtimeScenePrefetchStatus": {
                    "status": "ready",
                    "totalEntries": 2,
                    "loadedEntries": 2,
                    "pendingEntries": 0,
                },
                "runtimeScenePrefetchManifest": {
                    "prefetchKey": "scene_opening:b2:2|scene_branch|bg_branch,voice_branch",
                    "targetSceneIds": ["scene_branch"],
                    "entries": [
                        {"assetId": "bg_branch", "type": "background", "sizeBytes": 1024},
                        {"assetId": "voice_branch", "type": "voice", "sizeBytes": 2048},
                    ],
                },
                "imageCache": {"bg": object(), "missing": None},
                "soundCache": {"voice": object()},
                "videoPreviewFrameCache": {"op": object()},
                "runtimeScenePrefetchedAssetIds": {"bg_branch", "voice_branch"},
                "currentBgmAssetId": "bgm_theme",
                "voicePlaybackActive": True,
            }
        )

        self.assertEqual(report["status"], "warming")
        self.assertEqual(report["warningCount"], 2)
        section_titles = [section["title"] for section in report["sections"]]
        self.assertEqual(section_titles, ["播放位置", "启动预热", "路线预取", "运行缓存"])

        rows = [row for section in report["sections"] for row in section["rows"]]
        by_label = {row["label"]: row for row in rows}
        self.assertEqual(by_label["当前位置"]["value"], "Opening")
        self.assertEqual(by_label["剧情块"]["value"], "第 3 块")
        self.assertEqual(by_label["全局资源预热"]["value"], "3/5")
        self.assertEqual(by_label["后台剩余"]["value"], "2 项")
        self.assertEqual(by_label["路线预取"]["value"], "2/2")
        self.assertIn("图片 1 / 音频 1 / 视频 0", by_label["路线预取"]["detail"])
        self.assertEqual(by_label["分支预判"]["value"], "1 个场景")
        self.assertEqual(by_label["图片缓存"]["value"], "1 项")
        self.assertEqual(by_label["音频缓存"]["value"], "1 项")
        self.assertIn("BGM：bgm_theme", by_label["音频缓存"]["detail"])

    def test_runtime_diagnostics_report_flags_blocking_preload_issues(self) -> None:
        report = build_runtime_diagnostics_report(
            {
                "runtimePreloadStatus": {
                    "status": "blocked",
                    "totalEntries": 1,
                    "loadedEntries": 0,
                    "pendingEntries": 0,
                    "missingEntries": 1,
                },
                "runtimeScenePrefetchStatus": {"status": "empty"},
                "runtimeScenePrefetchManifest": {"entries": []},
            }
        )

        self.assertEqual(report["status"], "blocked")
        self.assertGreaterEqual(report["issueCount"], 1)
        self.assertIn("运行时异常", report["headline"])


if __name__ == "__main__":
    unittest.main()
