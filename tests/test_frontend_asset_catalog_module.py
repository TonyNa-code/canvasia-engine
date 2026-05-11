from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "asset_catalog.js"


class FrontendAssetCatalogModuleTests(unittest.TestCase):
    def test_asset_catalog_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorAssetCatalog;
            const mb = 1024 * 1024;
            const assetList = [
              {{ id: "bg_large", type: "background", name: "巨幅背景", fileExists: true, fileSizeBytes: 30 * mb }},
              {{ id: "video_warn", type: "video", name: "OP", fileExists: true, fileSizeBytes: 130 * mb }},
              {{ id: "voice_missing", type: "voice", name: "悠奈语音", fileExists: false, fileSizeBytes: 0 }},
              {{ id: "ui_unused", type: "ui", name: "按钮", fileExists: true, fileSizeBytes: 1024 }},
              {{ id: "custom", type: "custom", name: "自定义", fileExists: true, fileSizeBytes: 999 }},
            ];
            const data = {{
              assetList,
              assetUsage: new Map([
                ["bg_large", [{{ sceneId: "scene_a" }}]],
                ["voice_missing", [{{ sceneId: "scene_a", blockId: "block_1" }}]],
              ]),
            }};
            const gapDuplicateOverview = {{
              count: 3,
              perTypeMap: new Map([
                ["background", {{ duplicateCount: 1 }}],
                ["ui", {{ duplicateCount: 2 }}],
              ]),
            }};
            const mediaReport = tools.buildAssetMediaBudgetReport(data);
            const gapOverview = tools.buildAssetGapOverview(data, gapDuplicateOverview);
            const duplicateAssetList = [
              {{
                id: "bg_master",
                type: "background",
                name: "雨夜背景",
                path: "assets/bg/rain.png",
                fileExists: true,
                favorite: true,
                tags: ["主线", "夜晚"],
                fileSizeBytes: 2048,
              }},
              {{
                id: "bg_copy",
                type: "background",
                name: "雨夜背景 副本",
                path: "assets/bg/rain.png",
                fileExists: true,
                favorite: false,
                tags: [],
                fileSizeBytes: 1024,
              }},
              {{
                id: "bg_same_name",
                type: "background",
                name: "雨夜背景",
                path: "assets/bg/rain_v2.png",
                fileExists: false,
                favorite: false,
                tags: [],
                fileSizeBytes: 0,
              }},
              {{
                id: "voice_a",
                type: "voice",
                name: "line 01",
                path: "voice/line01.wav",
                fileExists: true,
                favorite: false,
                tags: [],
                fileSizeBytes: 4096,
              }},
              {{
                id: "voice_b",
                type: "voice",
                name: "line01 copy",
                path: "voice/line01.ogg",
                fileExists: false,
                favorite: false,
                tags: [],
                fileSizeBytes: 0,
              }},
            ];
            const duplicateData = {{
              assetList: duplicateAssetList,
              assetsById: new Map(duplicateAssetList.map((asset) => [asset.id, asset])),
              assetUsage: new Map([
                ["bg_master", [{{ sceneId: "scene_a" }}, {{ sceneId: "scene_b" }}]],
                ["bg_same_name", [{{ sceneId: "scene_c" }}]],
              ]),
            }};
            const duplicateOverview = tools.buildAssetDuplicateOverview(duplicateData);
            const masterDuplicateInfo = duplicateOverview.infoByAssetId.get("bg_master");
            const backgroundCluster = duplicateOverview.clusterByAssetId.get("bg_master");
            const visibleData = {{
              assetList: [
                {{
                  id: "bg_master",
                  type: "background",
                  name: "雨夜背景",
                  path: "assets/bg/rain.png",
                  fileExists: true,
                  favorite: true,
                  tags: ["主线", "夜晚"],
                  fileSizeBytes: 30 * mb,
                }},
                {{
                  id: "bg_copy",
                  type: "background",
                  name: "雨夜背景 副本",
                  path: "assets/bg/rain.png",
                  fileExists: true,
                  favorite: false,
                  tags: ["夜晚"],
                  fileSizeBytes: 1024,
                }},
                {{
                  id: "voice_missing",
                  type: "voice",
                  name: "悠奈语音",
                  path: "voices/yuina_001.wav",
                  fileExists: false,
                  favorite: true,
                  tags: ["女主"],
                  fileSizeBytes: 0,
                }},
                {{
                  id: "video_warn",
                  type: "video",
                  name: "OP 预览",
                  path: "video/op.mp4",
                  fileExists: true,
                  favorite: false,
                  tags: ["OP"],
                  fileSizeBytes: 130 * mb,
                }},
                {{
                  id: "model_risk",
                  type: "scene3d",
                  name: "3D 房间",
                  path: "3d/room.glb",
                  fileExists: true,
                  favorite: false,
                  tags: ["3D"],
                  fileSizeBytes: 10 * mb,
                }},
              ],
              assetUsage: new Map([
                ["bg_master", [{{ sceneId: "scene_a" }}, {{ sceneId: "scene_b" }}]],
                ["voice_missing", [{{ sceneId: "scene_a", blockId: "block_voice" }}]],
                ["model_risk", [{{ sceneId: "scene_3d" }}]],
              ]),
            }};
            visibleData.assetsById = new Map(visibleData.assetList.map((asset) => [asset.id, asset]));
            const visibleDuplicateOverview = tools.buildAssetDuplicateOverview(visibleData);
            const result = {{
              backgroundLabel: tools.getAssetTypeLabel("background"),
              modelLabel: tools.getAssetTypeLabel("model3d"),
              unknownLabel: tools.getAssetTypeLabel("custom"),
              videoTags: tools.getAssetPresetTags("video"),
              safePresentation: tools.getSafeCharacterPresentationMode("unknown"),
              live2dPresentation: tools.getCharacterPresentationModeLabel("live2d"),
              safeFilter: tools.getSafeAssetFilterMode(" media_budget "),
              badFilter: tools.getSafeAssetFilterMode("broken"),
              filterLabel: tools.getAssetFilterModeLabel("asset3d_risk"),
              filterStatus: tools.getAssetFilterModeStatusLabel("media_budget"),
              videoWarnBytes: tools.getAssetMediaBudgetLimit({{ type: "video" }}).warnBytes,
              missingLimit: tools.getAssetMediaBudgetLimit({{ type: "custom" }}),
              typeChecks: [
                tools.isImageAssetType("cg"),
                tools.isAudioAssetType("voice"),
                tools.isVideoAssetType("video"),
                tools.isScene3dAssetType("scene3d"),
                tools.isImageAssetType("bgm"),
              ],
              assetState: [
                tools.isAssetMissingFile(assetList[2]),
                tools.isAssetMissingFile(assetList[0]),
                tools.getAssetUsageCount("bg_large", data),
                tools.isAssetUnused("ui_unused", data),
                tools.isAssetUrgentMissing(assetList[2], data),
                tools.getUnusedAssets(data).map((asset) => asset.id),
              ],
              mediaRisk: [
                tools.getAssetMediaBudgetRisk(assetList[0]),
                tools.getAssetMediaBudgetRisk(assetList[1]),
                tools.getAssetMediaBudgetRisk(assetList[2]),
              ],
              mediaReport: {{
                count: mediaReport.count,
                blockerCount: mediaReport.blockerCount,
                warnCount: mediaReport.warnCount,
                totalLabel: mediaReport.totalLabel,
                largestId: mediaReport.largest.assetId,
                assetIds: Array.from(mediaReport.assetIds).sort(),
                perType: mediaReport.perType.map((entry) => [entry.type, entry.count]),
              }},
              gapOverview: {{
                totalCount: gapOverview.totalCount,
                readyCount: gapOverview.readyCount,
                missingCount: gapOverview.missingCount,
                urgentMissingCount: gapOverview.urgentMissingCount,
                unusedCount: gapOverview.unusedCount,
                duplicateCount: gapOverview.duplicateCount,
                priorityTypes: gapOverview.priorityTypes.map((entry) => [entry.type, entry.missingCount, entry.duplicateCount]),
              }},
              summaries: [
                tools.getAssetTypeGapSummaryText("voice", null, data, gapDuplicateOverview),
                tools.getAssetTypeGapSummaryText("background", null, data, gapDuplicateOverview),
                tools.getAssetTypeGapSummaryText("custom", null, data, gapDuplicateOverview),
                tools.getAssetTypeGapSummaryText("font", null, data, gapDuplicateOverview),
              ],
              searchAndSort: [
                tools.normalizeAssetSearchQuery("  OP 预览  "),
                tools.getAssetSortLabel("favorite"),
                tools.getAssetSortLabel("custom_mode"),
                tools.formatFileSize(1536),
              ],
              duplicateTokens: [
                tools.normalizeAssetDuplicateToken("雨夜 背景 copy.png"),
                tools.normalizeAssetDuplicateToken("rain (2).png"),
                tools.getAssetPathBasename("a\\\\b/c.png"),
              ],
              duplicateOverview: {{
                count: duplicateOverview.count,
                assetIds: Array.from(duplicateOverview.assetIdSet).sort(),
                entries: duplicateOverview.entries.map((entry) => [
                  entry.assetId,
                  entry.relatedCount,
                  entry.score,
                  entry.preferredAssetId,
                  entry.isPreferred,
                  entry.tone,
                ]),
                clusters: duplicateOverview.clusters.map((cluster) => [
                  cluster.id,
                  [...cluster.assetIds].sort(),
                  cluster.preferredAssetId,
                  cluster.tone,
                  cluster.usedAssetsCount,
                  cluster.readyAssetsCount,
                  cluster.reasonLabels.map((label) => label.text),
                ]),
                priorityTypes: duplicateOverview.priorityTypes.map((entry) => [entry.type, entry.duplicateCount]),
                priorityClusterIds: duplicateOverview.priorityClusters.map((cluster) => cluster.id),
                bgReasonLabels: tools.getAssetDuplicateReasonLabels(masterDuplicateInfo).map((label) => label.text),
                bgCopyLabels: tools.getAssetDuplicateReasonLabels(masterDuplicateInfo, "bg_copy").map((label) => label.text),
                preferredScore: tools.getAssetDuplicatePreferenceScore(backgroundCluster.preferredAsset, duplicateData),
                preferredNotes: tools.buildAssetDuplicatePreferenceNotes(backgroundCluster.preferredAsset, duplicateData),
                preferredSummary: backgroundCluster.summary,
                preferredRecommendation: backgroundCluster.recommendation,
              }},
              visibleAssets: {{
                sortedRecent: tools.sortAssets(visibleData.assetList, "recent", visibleData).map((asset) => asset.id),
                sortedName: tools.sortAssets(visibleData.assetList, "name", visibleData).map((asset) => asset.id),
                sortedUsage: tools.sortAssets(visibleData.assetList, "usage", visibleData).map((asset) => asset.id),
                sortedFavorite: tools.sortAssets(visibleData.assetList, "favorite", visibleData).map((asset) => asset.id),
                unused: tools.getVisibleAssets(visibleData, {{ filterMode: "unused" }}).map((asset) => asset.id),
                missing: tools.getVisibleAssets(visibleData, {{ filterMode: "missing_file" }}).map((asset) => asset.id),
                urgent: tools.getVisibleAssets(visibleData, {{ filterMode: "urgent_missing" }}).map((asset) => asset.id),
                mediaBudget: tools.getVisibleAssets(visibleData, {{ filterMode: "media_budget" }}).map((asset) => asset.id),
                asset3dRisk: tools.getVisibleAssets(visibleData, {{
                  filterMode: "asset3d_risk",
                  nativeRuntime3dRiskAssetIds: ["model_risk", "missing"],
                }}).map((asset) => asset.id),
                duplicateDefault: tools.getVisibleAssets(visibleData, {{
                  filterMode: "duplicate",
                  duplicateOverview: visibleDuplicateOverview,
                }}).map((asset) => asset.id),
                duplicateName: tools.getVisibleAssets(visibleData, {{
                  filterMode: "duplicate",
                  sortMode: "name",
                  duplicateOverview: visibleDuplicateOverview,
                }}).map((asset) => asset.id),
                nightFavorite: tools.getVisibleAssets(visibleData, {{
                  tagFilter: "夜晚",
                  favoriteOnly: true,
                }}).map((asset) => asset.id),
                searchType: tools.getVisibleAssets(visibleData, {{
                  searchQuery: "视频",
                }}).map((asset) => asset.id),
                searchPath: tools.getVisibleAssets(visibleData, {{
                  searchQuery: "room.glb",
                }}).map((asset) => asset.id),
              }},
              checkedAssets: {{
                pruned: tools.pruneAssetCheckedIds(
                  [" bg_master ", "missing", "bg_master", "", null, "voice_missing"],
                  visibleData
                ),
                checked: tools.getCheckedAssetIds(
                  [" bg_master ", "missing", "bg_master", "", null, "voice_missing"],
                  visibleData
                ),
                currentBackgroundAll: tools.getCurrentFilteredAssetsOfSelectedType(
                  visibleData,
                  "background"
                ).map((asset) => asset.id),
                currentBackgroundNight: tools.getCurrentFilteredAssetsOfSelectedType(
                  visibleData,
                  "background",
                  {{ tagFilter: "夜晚" }}
                ).map((asset) => asset.id),
                currentCheckedIds: tools.getCurrentCheckedAssetIds(
                  ["bg_copy", "voice_missing", "bg_master", "missing", "bg_copy"],
                  visibleData,
                  "background",
                  {{ tagFilter: "夜晚" }}
                ),
                currentCheckedAssets: tools.getCurrentCheckedAssetsOfSelectedType(
                  ["bg_copy", "voice_missing", "bg_master", "missing", "bg_copy"],
                  visibleData,
                  "background",
                  {{ tagFilter: "夜晚" }}
                ).map((asset) => asset.id),
                hiddenBySearch: tools.getCurrentCheckedAssetIds(
                  ["bg_copy", "bg_master"],
                  visibleData,
                  "background",
                  {{ searchQuery: "视频" }}
                ),
                isChecked: [
                  tools.isAssetChecked("voice_missing", [" voice_missing ", "missing"], visibleData),
                  tools.isAssetChecked("missing", [" voice_missing ", "missing"], visibleData),
                ],
                toggle: [
                  tools.toggleAssetChecked(["bg_master"], "bg_copy", true, visibleData),
                  tools.toggleAssetChecked(["bg_master"], "missing", true, visibleData),
                  tools.toggleAssetChecked(["bg_master", "bg_copy"], "bg_master", false, visibleData),
                ],
              }},
              tagOperations: {{
                parsed: tools.parseAssetTagsInput("  夜晚,主线，夜晚、 女主 ; ; OP\\n3D "),
                zeroLimit: tools.parseAssetTagsInput("a,b", {{ limit: 0 }}),
                limited: tools.parseAssetTagsInput("a,b,c,d", {{ limit: 2 }}),
                safeAssetIds: [
                  tools.getSafeAssetIdByType("background", "bg_copy", visibleData),
                  tools.getSafeAssetIdByType("background", "missing", visibleData),
                  tools.getSafeAssetIdByType("font", "missing", visibleData),
                ],
                bulkAddChecked: tools.buildBulkAssetTagOperation(
                  "add",
                  "夜晚, 主线, 夜晚",
                  [visibleData.assetList[0], visibleData.assetList[1]],
                  [visibleData.assetList[3]],
                  {{ limit: 8 }}
                ),
                bulkRemoveFiltered: tools.buildBulkAssetTagOperation(
                  "remove",
                  "OP",
                  [],
                  [visibleData.assetList[3]],
                  {{ limit: 8 }}
                ),
                bulkNoTags: tools.buildBulkAssetTagOperation(
                  "add",
                  " , ",
                  [visibleData.assetList[0]],
                  [visibleData.assetList[3]]
                ),
                bulkNoAssets: tools.buildBulkAssetTagOperation(
                  "remove",
                  "OP",
                  [],
                  []
                ),
                presetChecked: tools.buildPresetAssetTagOperation(
                  " 推荐 ",
                  [visibleData.assetList[0], visibleData.assetList[1]],
                  visibleData.assetList[3]
                ),
                presetSelected: tools.buildPresetAssetTagOperation(
                  "OP",
                  [],
                  visibleData.assetList[3]
                ),
                presetEmpty: tools.buildPresetAssetTagOperation(
                  " ",
                  [],
                  visibleData.assetList[3]
                ),
                presetNoAssets: tools.buildPresetAssetTagOperation(
                  "OP",
                  [],
                  null
                ),
              }},
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
        self.assertEqual(payload["backgroundLabel"], "背景")
        self.assertEqual(payload["modelLabel"], "3D 模型")
        self.assertEqual(payload["unknownLabel"], "custom")
        self.assertEqual(payload["videoTags"], ["OP", "ED", "PV", "过场"])
        self.assertEqual(payload["safePresentation"], "sprite")
        self.assertEqual(payload["live2dPresentation"], "Live2D")
        self.assertEqual(payload["safeFilter"], "media_budget")
        self.assertEqual(payload["badFilter"], "all")
        self.assertEqual(payload["filterLabel"], "仅看 3D 发布风险")
        self.assertIn("体积偏大", payload["filterStatus"])
        self.assertEqual(payload["videoWarnBytes"], 120 * 1024 * 1024)
        self.assertIsNone(payload["missingLimit"])
        self.assertEqual(payload["typeChecks"], [True, True, True, True, False])
        self.assertEqual(
            payload["assetState"],
            [True, False, 1, True, True, ["video_warn", "ui_unused", "custom"]],
        )
        self.assertEqual(payload["mediaRisk"][0]["severity"], "blocker")
        self.assertEqual(payload["mediaRisk"][0]["fileSizeLabel"], "30 MB")
        self.assertEqual(payload["mediaRisk"][0]["warnLabel"], "8.0 MB")
        self.assertIn("WebP", payload["mediaRisk"][0]["suggestion"])
        self.assertEqual(payload["mediaRisk"][1]["severity"], "warn")
        self.assertIn("H.264", payload["mediaRisk"][1]["suggestion"])
        self.assertIsNone(payload["mediaRisk"][2])
        self.assertEqual(payload["mediaReport"]["count"], 2)
        self.assertEqual(payload["mediaReport"]["blockerCount"], 1)
        self.assertEqual(payload["mediaReport"]["warnCount"], 1)
        self.assertEqual(payload["mediaReport"]["totalLabel"], "160 MB")
        self.assertEqual(payload["mediaReport"]["largestId"], "bg_large")
        self.assertEqual(payload["mediaReport"]["assetIds"], ["bg_large", "video_warn"])
        self.assertEqual(payload["mediaReport"]["perType"], [["background", 1], ["video", 1]])
        self.assertEqual(
            payload["gapOverview"],
            {
                "totalCount": 5,
                "readyCount": 4,
                "missingCount": 1,
                "urgentMissingCount": 1,
                "unusedCount": 3,
                "duplicateCount": 3,
                "priorityTypes": [["voice", 1, 0], ["ui", 0, 2], ["background", 0, 1]],
            },
        )
        self.assertEqual(
            payload["summaries"],
            [
                "全量 1 个里待导入 1 个，其中已引用缺口 1 个",
                "全量 1 个素材都已经就绪，当前重点是整理疑似重复 1 个",
                "全量 1 个素材都已经导入完成",
                "这一类暂时还没有素材",
            ],
        )
        self.assertEqual(payload["searchAndSort"], ["op 预览", "收藏优先", "custom_mode", "1.5 KB"])
        self.assertEqual(payload["duplicateTokens"], ["雨夜背景", "rain", "c.png"])
        self.assertEqual(payload["duplicateOverview"]["count"], 5)
        self.assertEqual(
            payload["duplicateOverview"]["assetIds"],
            ["bg_copy", "bg_master", "bg_same_name", "voice_a", "voice_b"],
        )
        self.assertEqual(payload["duplicateOverview"]["entries"][0][0], "bg_master")
        self.assertEqual(payload["duplicateOverview"]["entries"][0][3], "bg_master")
        self.assertTrue(payload["duplicateOverview"]["entries"][0][4])
        self.assertEqual(payload["duplicateOverview"]["entries"][0][5], "danger")
        self.assertEqual(len(payload["duplicateOverview"]["clusters"]), 2)
        self.assertEqual(
            payload["duplicateOverview"]["clusters"][0],
            [
                "duplicate_cluster_1",
                ["bg_copy", "bg_master", "bg_same_name"],
                "bg_master",
                "danger",
                2,
                2,
                ["同一路径", "名字几乎一样", "文件名几乎一样"],
            ],
        )
        self.assertEqual(
            payload["duplicateOverview"]["clusters"][1],
            [
                "duplicate_cluster_2",
                ["voice_a", "voice_b"],
                "voice_a",
                "soft",
                0,
                1,
                ["名字几乎一样", "文件名几乎一样"],
            ],
        )
        self.assertEqual(payload["duplicateOverview"]["priorityTypes"], [["background", 3], ["voice", 2]])
        self.assertEqual(payload["duplicateOverview"]["priorityClusterIds"], ["duplicate_cluster_1", "duplicate_cluster_2"])
        self.assertEqual(
            payload["duplicateOverview"]["bgReasonLabels"],
            ["同一路径", "名字几乎一样", "文件名几乎一样"],
        )
        self.assertEqual(
            payload["duplicateOverview"]["bgCopyLabels"],
            ["同一路径", "名字几乎一样", "文件名几乎一样"],
        )
        self.assertGreater(payload["duplicateOverview"]["preferredScore"], 250)
        self.assertEqual(
            payload["duplicateOverview"]["preferredNotes"],
            ["已经被剧情使用 2 处", "真实文件已经就绪", "你已经收藏过它"],
        )
        self.assertEqual(payload["duplicateOverview"]["preferredSummary"], "这一组共 3 项，优先保留 雨夜背景")
        self.assertIn("已经有 2 项被剧情引用", payload["duplicateOverview"]["preferredRecommendation"])
        self.assertEqual(
            payload["visibleAssets"],
            {
                "sortedRecent": ["model_risk", "video_warn", "voice_missing", "bg_copy", "bg_master"],
                "sortedName": ["model_risk", "voice_missing", "bg_master", "bg_copy", "video_warn"],
                "sortedUsage": ["bg_master", "model_risk", "voice_missing", "bg_copy", "video_warn"],
                "sortedFavorite": ["bg_master", "voice_missing", "model_risk", "bg_copy", "video_warn"],
                "unused": ["bg_copy", "video_warn"],
                "missing": ["voice_missing"],
                "urgent": ["voice_missing"],
                "mediaBudget": ["bg_master", "video_warn"],
                "asset3dRisk": ["model_risk"],
                "duplicateDefault": ["bg_master", "bg_copy"],
                "duplicateName": ["bg_master", "bg_copy"],
                "nightFavorite": ["bg_master"],
                "searchType": ["video_warn"],
                "searchPath": ["model_risk"],
            },
        )
        self.assertEqual(
            payload["checkedAssets"],
            {
                "pruned": ["bg_master", "voice_missing"],
                "checked": ["bg_master", "voice_missing"],
                "currentBackgroundAll": ["bg_master", "bg_copy"],
                "currentBackgroundNight": ["bg_master", "bg_copy"],
                "currentCheckedIds": ["bg_copy", "bg_master"],
                "currentCheckedAssets": ["bg_master", "bg_copy"],
                "hiddenBySearch": [],
                "isChecked": [True, False],
                "toggle": [["bg_master", "bg_copy"], ["bg_master"], ["bg_copy"]],
            },
        )
        self.assertEqual(payload["tagOperations"]["parsed"], ["夜晚", "主线", "女主", "OP", "3D"])
        self.assertEqual(payload["tagOperations"]["zeroLimit"], [])
        self.assertEqual(payload["tagOperations"]["limited"], ["a", "b"])
        self.assertEqual(payload["tagOperations"]["safeAssetIds"], ["bg_copy", "bg_master", ""])
        self.assertEqual(payload["tagOperations"]["bulkAddChecked"]["mode"], "add")
        self.assertEqual(payload["tagOperations"]["bulkAddChecked"]["tags"], ["夜晚", "主线"])
        self.assertEqual(payload["tagOperations"]["bulkAddChecked"]["assetIds"], ["bg_master", "bg_copy"])
        self.assertEqual(payload["tagOperations"]["bulkAddChecked"]["actionLabel"], "添加")
        self.assertEqual(payload["tagOperations"]["bulkAddChecked"]["targetLabel"], "当前勾选的 2 个素材")
        self.assertEqual(payload["tagOperations"]["bulkAddChecked"]["targetScope"], "checked")
        self.assertTrue(payload["tagOperations"]["bulkAddChecked"]["canApply"])
        self.assertIn("夜晚 / 主线", payload["tagOperations"]["bulkAddChecked"]["confirmationMessage"])
        self.assertEqual(payload["tagOperations"]["bulkRemoveFiltered"]["mode"], "remove")
        self.assertEqual(payload["tagOperations"]["bulkRemoveFiltered"]["assetIds"], ["video_warn"])
        self.assertEqual(payload["tagOperations"]["bulkRemoveFiltered"]["actionLabel"], "移除")
        self.assertEqual(payload["tagOperations"]["bulkRemoveFiltered"]["targetScope"], "filtered")
        self.assertEqual(payload["tagOperations"]["bulkNoTags"]["error"], "no_tags")
        self.assertFalse(payload["tagOperations"]["bulkNoTags"]["canApply"])
        self.assertEqual(payload["tagOperations"]["bulkNoAssets"]["error"], "no_assets")
        self.assertFalse(payload["tagOperations"]["bulkNoAssets"]["canApply"])
        self.assertEqual(payload["tagOperations"]["presetChecked"]["tag"], "推荐")
        self.assertEqual(payload["tagOperations"]["presetChecked"]["assetIds"], ["bg_master", "bg_copy"])
        self.assertEqual(payload["tagOperations"]["presetChecked"]["targetLabel"], "勾选的 2 个素材")
        self.assertEqual(payload["tagOperations"]["presetChecked"]["targetScope"], "checked")
        self.assertTrue(payload["tagOperations"]["presetChecked"]["canApply"])
        self.assertEqual(payload["tagOperations"]["presetSelected"]["assetIds"], ["video_warn"])
        self.assertEqual(payload["tagOperations"]["presetSelected"]["targetScope"], "selected")
        self.assertEqual(payload["tagOperations"]["presetEmpty"]["error"], "no_tag")
        self.assertFalse(payload["tagOperations"]["presetEmpty"]["canApply"])
        self.assertEqual(payload["tagOperations"]["presetNoAssets"]["error"], "no_assets")
        self.assertFalse(payload["tagOperations"]["presetNoAssets"]["canApply"])


if __name__ == "__main__":
    unittest.main()
