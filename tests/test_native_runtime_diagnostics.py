from __future__ import annotations

import unittest

from native_runtime.runtime_diagnostics import (
    build_export_runtime_diagnostics_report,
    build_runtime_cache_efficiency_summary,
    build_runtime_diagnostics_report,
    render_export_runtime_diagnostics_markdown,
)


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
                    "cachedEntries": 1,
                },
                "runtimeScenePrefetchStatus": {
                    "status": "ready",
                    "totalEntries": 2,
                    "loadedEntries": 2,
                    "pendingEntries": 0,
                    "cachedEntries": 1,
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
                "controllerStatus": {
                    "connectedCount": 1,
                    "connected": True,
                    "names": ["Wireless Controller"],
                    "label": "1 个 · Wireless Controller",
                },
            }
        )

        self.assertEqual(report["status"], "warming")
        self.assertEqual(report["warningCount"], 3)
        self.assertEqual(report["cacheEfficiency"]["totalEntries"], 7)
        self.assertEqual(report["cacheEfficiency"]["readyEntries"], 5)
        self.assertEqual(report["cacheEfficiency"]["cachedEntries"], 2)
        self.assertEqual(report["cacheEfficiency"]["readyPercent"], 71)
        self.assertEqual(report["cacheEfficiency"]["reusePercent"], 29)
        section_titles = [section["title"] for section in report["sections"]]
        self.assertEqual(section_titles, ["播放位置", "启动预热", "路线预取", "运行缓存"])

        rows = [row for section in report["sections"] for row in section["rows"]]
        by_label = {row["label"]: row for row in rows}
        self.assertEqual(by_label["当前位置"]["value"], "Opening")
        self.assertEqual(by_label["剧情块"]["value"], "第 3 块")
        self.assertEqual(by_label["手柄输入"]["value"], "1 个 · Wireless Controller")
        self.assertEqual(by_label["手柄输入"]["tone"], "ready")
        self.assertEqual(by_label["全局资源预热"]["value"], "3/5")
        self.assertEqual(by_label["后台剩余"]["value"], "2 项")
        self.assertEqual(by_label["路线预取"]["value"], "2/2")
        self.assertIn("图片 1 / 音频 1 / 视频 0", by_label["路线预取"]["detail"])
        self.assertEqual(by_label["分支预判"]["value"], "1 个场景")
        self.assertEqual(by_label["图片缓存"]["value"], "1 项")
        self.assertEqual(by_label["音频缓存"]["value"], "1 项")
        self.assertIn("BGM：bgm_theme", by_label["音频缓存"]["detail"])
        self.assertEqual(by_label["缓存复用效率"]["value"], "2/7")
        self.assertIn("运行准备率 71%", by_label["缓存复用效率"]["detail"])
        self.assertIn("复用率 29%", by_label["缓存复用效率"]["detail"])

    def test_runtime_cache_efficiency_summary_handles_empty_and_cached_states(self) -> None:
        empty = build_runtime_cache_efficiency_summary({})
        cached = build_runtime_cache_efficiency_summary(
            {
                "runtimePreloadStatus": {
                    "totalEntries": 2,
                    "readyEntries": 2,
                    "pendingEntries": 0,
                    "cachedEntries": 1,
                },
                "runtimeScenePrefetchStatus": {
                    "totalEntries": 2,
                    "loadedEntries": 1,
                    "pendingEntries": 1,
                    "cachedEntries": 1,
                },
                "imageCache": {"bg": object(), "missing": None},
                "soundCache": {"voice": object()},
            }
        )

        self.assertEqual(empty["status"], "empty")
        self.assertEqual(empty["readyPercent"], 0)
        self.assertEqual(cached["status"], "warming")
        self.assertEqual(cached["totalEntries"], 4)
        self.assertEqual(cached["readyEntries"], 3)
        self.assertEqual(cached["cachedEntries"], 2)
        self.assertEqual(cached["loadedCacheEntries"], 2)
        self.assertEqual(cached["readyPercent"], 75)
        self.assertEqual(cached["reusePercent"], 50)

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

    def test_export_runtime_diagnostics_report_renders_static_release_evidence(self) -> None:
        payload = {
            "project": {
                "projectId": "proj_demo",
                "title": "Release Demo",
                "language": "zh-CN",
                "entrySceneId": "scene_opening",
            },
            "assets": {
                "assets": [
                    {
                        "id": "bg_school",
                        "name": "School Gate",
                        "type": "background",
                        "exportUrl": "assets/bg_school.png",
                        "fileSizeBytes": 2048,
                    }
                ]
            },
            "characters": {"characters": []},
            "chapters": [
                {
                    "id": "ch1",
                    "scenes": [
                        {
                            "id": "scene_opening",
                            "name": "Opening",
                            "blocks": [
                                {"id": "b1", "type": "narration", "text": "Morning."},
                                {"id": "b2", "type": "background", "assetId": "bg_school"},
                            ],
                        }
                    ],
                }
            ],
        }
        preload_report = {
            "status": "ready",
            "recommendation": "资源预热清单和包内素材路径可用。",
            "summary": {
                "status": "ready",
                "totalEntries": 1,
                "imageEntries": 1,
                "soundEntries": 0,
                "streamEntries": 0,
                "missingFileEntries": 0,
            },
        }

        report = build_export_runtime_diagnostics_report(payload, preload_report, bundle_dir="/tmp/demo")
        markdown = render_export_runtime_diagnostics_markdown(report)

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["project"]["title"], "Release Demo")
        self.assertEqual(report["entry"]["sceneName"], "Opening")
        self.assertEqual(report["summary"]["preloadEntries"], 1)
        self.assertEqual(report["summary"]["prefetchEntries"], 1)
        self.assertEqual(report["summary"]["cacheReadyPercent"], 100)
        self.assertEqual(report["summary"]["cacheReusePercent"], 0)
        self.assertIn("runtime-diagnostics-report", " ".join(report["recommendedCommands"]))
        self.assertIn("# 原生 Runtime 运行诊断报告", markdown)
        self.assertIn("运行准备率 / 复用率", markdown)
        self.assertIn("School Gate", markdown)


if __name__ == "__main__":
    unittest.main()
