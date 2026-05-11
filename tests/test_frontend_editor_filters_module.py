from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "editor_filters.js"


class FrontendEditorFiltersModuleTests(unittest.TestCase):
    def test_editor_filter_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorFilters;
            const routeNodes = [
              {{
                hasStoryContent: true,
                hasBackground: false,
                hasMusic: true,
                hasEffects: false,
                missingVoiceCount: 0,
                completionScore: 42,
                errorCount: 0,
                warningCount: 0,
                brokenRouteCount: 0,
              }},
              {{
                hasStoryContent: true,
                hasBackground: true,
                hasMusic: false,
                hasEffects: true,
                missingVoiceCount: 2,
                completionScore: 86,
                errorCount: 1,
                warningCount: 0,
                brokenRouteCount: 0,
              }},
              {{
                hasStoryContent: false,
                hasBackground: false,
                hasMusic: false,
                hasEffects: false,
                missingVoiceCount: 0,
                completionScore: 0,
                errorCount: 0,
                warningCount: 0,
                brokenRouteCount: 0,
              }},
            ];
            const result = {{
              keys: Object.keys(tools).sort(),
              labels: {{
                dashboard: [
                  tools.getDashboardSearchModeLabel("all"),
                  tools.getDashboardSearchModeLabel("characters"),
                  tools.getDashboardSearchModeLabel("broken"),
                ],
                route: [
                  tools.getRouteMapFilterLabel("missing_music"),
                  tools.getRouteMapFilterLabel("broken"),
                ],
                scene: [
                  tools.getSceneStatusLabel("ready"),
                  tools.getSceneStatusLabel("broken"),
                  tools.getScenePriorityLabel("rush"),
                  tools.getScenePriorityLabel("broken"),
                ],
                story: [
                  tools.getStoryBlockTypeFilterLabel("logic"),
                  tools.getStoryBlockTypeFilterLabel("broken"),
                  tools.getStoryBlockIssueFilterLabel("variable_logic"),
                  tools.getStoryBlockIssueFilterLabel("broken"),
                  tools.getStorySceneTreeFilterLabel("notes"),
                  tools.getStorySceneTreeFilterLabel("broken"),
                ],
                characterAndPreview: [
                  tools.getCharacterFilterLabel("major"),
                  tools.getCharacterFilterLabel("broken"),
                  tools.getPreviewIssueFilterLabel("media_budget"),
                  tools.getPreviewIssueFilterLabel("broken"),
                  tools.getPreviewSceneFilterLabel("ready"),
                  tools.getPreviewSceneFilterLabel("broken"),
                ],
                script: [
                  tools.getScriptTypeLabel("all"),
                  tools.getScriptTypeLabel("dialogue"),
                  tools.getScriptTypeLabel("broken"),
                  tools.getScriptVoiceFilterLabel("voiced"),
                  tools.getScriptVoiceFilterLabel("broken"),
                  tools.getScriptIssueFilterLabel("duplicate"),
                  tools.getScriptIssueFilterLabel("broken"),
                ],
              }},
              safeValues: [
                tools.getSafeDashboardSearchMode("lines"),
                tools.getSafeDashboardSearchMode(" lines "),
                tools.getSafeRouteMapFilter("ready"),
                tools.getSafeSceneStatus("polishing"),
                tools.getSafeSceneStatus(null),
                tools.getSafeScenePriority("parked"),
                tools.getSafeStoryBlockTypeFilter("video"),
                tools.getSafeStoryBlockIssueFilter("missing_asset"),
                tools.getSafeStorySceneTreeFilter("focus"),
                tools.getSafeCharacterFilterMode("silent"),
                tools.getSafePreviewIssueFilterMode("errors"),
                tools.getSafePreviewSceneFilterMode("issues"),
                tools.getSafeScriptTypeFilter("choice"),
                tools.getSafeScriptTypeFilter("all"),
                tools.getSafeScriptTypeFilter("broken"),
                tools.getSafeScriptVoiceFilter("not_required"),
                tools.getSafeScriptIssueFilter("placeholder"),
              ],
              tones: [
                tools.getSceneStatusToneClass("ready"),
                tools.getSceneStatusToneClass("polishing"),
                tools.getSceneStatusToneClass("drafting"),
                tools.getScenePriorityToneClass("rush"),
                tools.getScenePriorityToneClass("focus"),
                tools.getScenePriorityToneClass("normal"),
                tools.getSceneQuickButtonToneClass("status", "ready"),
                tools.getSceneQuickButtonToneClass("status", "drafting"),
                tools.getSceneQuickButtonToneClass("priority", "rush"),
                tools.getSceneQuickButtonToneClass("priority", "focus"),
                tools.getSceneQuickButtonToneClass("priority", "parked"),
                tools.getSceneQuickButtonToneClass("priority", "normal"),
              ],
              routeMatches: {{
                all: routeNodes.map((node) => tools.doesRouteNodeMatchFilter(node, "all")),
                issues: routeNodes.map((node) => tools.doesRouteNodeMatchFilter(node, "issues")),
                missingBackground: routeNodes.map((node) => tools.doesRouteNodeMatchFilter(node, "missing_background")),
                missingMusic: routeNodes.map((node) => tools.doesRouteNodeMatchFilter(node, "missing_music")),
                missingVoice: routeNodes.map((node) => tools.doesRouteNodeMatchFilter(node, "missing_voice")),
                flat: routeNodes.map((node) => tools.doesRouteNodeMatchFilter(node, "flat")),
                empty: routeNodes.map((node) => tools.doesRouteNodeMatchFilter(node, "empty")),
                ready: routeNodes.map((node) => tools.doesRouteNodeMatchFilter(node, "ready")),
                fallback: routeNodes.map((node) => tools.doesRouteNodeMatchFilter(node, "broken")),
              }},
              routeCounts: [
                tools.getRouteMapFilterCount({{ nodes: routeNodes }}, "all"),
                tools.getRouteMapFilterCount({{ nodes: routeNodes }}, "issues"),
                tools.getRouteMapFilterCount({{ nodes: routeNodes }}, "ready"),
                tools.getRouteMapFilterCount({{ nodes: null }}, "all"),
              ],
              storyGroups: [
                tools.getStoryBlockGroup("dialogue"),
                tools.getStoryBlockGroup("choice"),
                tools.getStoryBlockGroup("jump"),
                tools.getStoryBlockGroup("variable_add"),
                tools.getStoryBlockGroup("video_play"),
                tools.getStoryBlockGroupLabel("narration"),
                tools.getStoryBlockGroupLabel("condition"),
                tools.getStoryBlockGroupLabel("particle_effect"),
              ],
              search: {{
                normalized: tools.normalizeDashboardSearchQuery("  Heroine   雨夜  "),
                terms: tools.getDashboardSearchTerms("  Heroine   雨夜  "),
                emptyTerms: tools.getDashboardSearchTerms("   "),
                scriptNormalized: tools.normalizeScriptSearchQuery("  Voice   台词  "),
                scriptTerms: tools.getScriptSearchTerms("  Voice   台词  "),
                matches: [
                  tools.doesSearchTextMatchTerms("雨夜校园 女主", ["雨夜", "女主"]),
                  tools.doesSearchTextMatchTerms("雨夜校园 女主", ["雨夜", "男主"]),
                  tools.doesSearchTextMatchTerms("雨夜校园 女主", []),
                  tools.doesSearchTextMatchTerms("雨夜校园 女主", "  雨夜   女主  "),
                ],
              }},
              searchScores: [
                tools.scoreDashboardSearchMatch("雨夜校园", ["雨夜校园", "女主"], "雨夜", ["雨夜"]),
                tools.scoreDashboardSearchMatch("校园雨夜", ["校园雨夜", "女主"], "雨夜", ["雨夜"]),
                tools.scoreDashboardSearchMatch("女主", ["雨夜校园", "女主"], "雨夜", ["雨夜"]),
                tools.scoreDashboardSearchMatch("女主", ["阳光校园"], "雨夜", ["雨夜"]),
                tools.scoreDashboardSearchMatch("女主", ["雨夜校园"], "", []),
              ],
              sortedTitles: tools.sortDashboardSearchResults([
                {{ title: "乙", score: 3 }},
                {{ title: "甲", score: 9 }},
                {{ title: "丙", score: 3 }},
                {{ title: "空分", score: null }},
              ]).map((item) => item.title),
              constants: [
                tools.DASHBOARD_SEARCH_MODE_LABELS.lines,
                tools.ROUTE_MAP_FILTER_LABELS.flat,
                tools.SCRIPT_ISSUE_FILTER_LABELS.missing_voice,
              ],
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
        self.assertIn("getSafeSceneStatus", payload["keys"])
        self.assertIn("getScriptIssueFilterLabel", payload["keys"])
        self.assertIn("doesRouteNodeMatchFilter", payload["keys"])
        self.assertIn("getStoryBlockGroup", payload["keys"])
        self.assertEqual(payload["labels"]["dashboard"], ["全部结果", "角色", "全部结果"])
        self.assertEqual(payload["labels"]["route"], ["缺 BGM", "全部场景"])
        self.assertEqual(payload["labels"]["scene"], ["可试玩", "写作中", "马上处理", "正常"])
        self.assertEqual(payload["labels"]["story"], [
            "只看逻辑",
            "全部卡片",
            "变量待修",
            "全部状态",
            "有便签",
            "全部场景",
        ])
        self.assertEqual(payload["labels"]["characterAndPreview"], [
            "台词较多",
            "全部角色",
            "素材预算",
            "全部检查",
            "可试玩",
            "全部起点",
        ])
        self.assertEqual(payload["labels"]["script"], [
            "全部内容",
            "台词",
            "全部内容",
            "已绑语音",
            "全部状态",
            "疑似重复",
            "全部问题状态",
        ])
        self.assertEqual(payload["safeValues"], [
            "lines",
            "all",
            "ready",
            "polishing",
            "drafting",
            "parked",
            "video",
            "missing_asset",
            "focus",
            "silent",
            "errors",
            "issues",
            "choice",
            "all",
            "all",
            "not_required",
            "placeholder",
        ])
        self.assertEqual(payload["tones"], [
            "good-text",
            "warn-text",
            "",
            "danger-text",
            "warn-text",
            "",
            "is-good",
            "is-soft",
            "is-danger",
            "is-warn",
            "is-muted",
            "is-soft",
        ])
        self.assertEqual(payload["routeMatches"], {
            "all": [True, True, True],
            "issues": [False, True, False],
            "missingBackground": [True, False, False],
            "missingMusic": [False, True, False],
            "missingVoice": [False, True, False],
            "flat": [True, False, False],
            "empty": [False, False, True],
            "ready": [False, True, False],
            "fallback": [True, True, True],
        })
        self.assertEqual(payload["routeCounts"], [3, 1, 1, 0])
        self.assertEqual(payload["storyGroups"], [
            "story",
            "story",
            "logic",
            "logic",
            "effect",
            "正文",
            "逻辑",
            "演出",
        ])
        self.assertEqual(payload["search"], {
            "normalized": "heroine 雨夜",
            "terms": ["heroine", "雨夜"],
            "emptyTerms": [],
            "scriptNormalized": "voice 台词",
            "scriptTerms": ["voice", "台词"],
            "matches": [True, False, True, True],
        })
        self.assertEqual(payload["searchScores"], [22, 14, 6, -1, -1])
        self.assertEqual(payload["sortedTitles"], ["甲", "丙", "乙", "空分"])
        self.assertEqual(payload["constants"], ["台词和选项", "演出偏素", "待绑语音"])


if __name__ == "__main__":
    unittest.main()
