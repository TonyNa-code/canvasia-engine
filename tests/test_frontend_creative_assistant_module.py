from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "creative_assistant.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"


class FrontendCreativeAssistantModuleTests(unittest.TestCase):
    def test_creative_assistant_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorCreativeAssistant;
            const record = tools.sanitizeCreativeAssistantHistoryRecord({{
              id: "",
              createdAt: "",
              prompt: "  写一个雨夜开场  ",
              sceneName: "",
              favorite: true,
              result: {{
                mode: "broken",
                title: "  雨夜秘密  ",
                summary: "  走廊灯忽明忽暗  ",
                guidance: ["  保持悬念  ", "", "增加脚步声"],
                assetPrompts: ["  雨夜走廊背景  "],
                provider: {{ mode: "openai", model: " gpt-test ", fallback: true }},
                privacy: {{ sentToExternalService: true, message: "  已发送  " }},
                blocks: [
                  {{ type: "dialogue", text: "  你听见了吗？  ", speakerId: " heroine ", expressionId: " worried " }},
                  {{ type: "choice", options: [
                    {{ text: "追上去", gotoSceneId: "next", effects: [{{ type: "legacy" }}] }},
                    {{ text: "", gotoSceneId: "" }},
                    {{ text: "留在原地" }},
                    {{ text: "呼喊" }},
                    {{ text: "第五个会被裁掉" }}
                  ] }},
                  {{ type: "legacy", text: "会转成旁白" }}
                ],
              }},
            }}, {{
              createId: () => "fixed_id",
              nowIso: () => "2026-05-04T00:00:00.000Z",
            }});
            const result = {{
              merged: tools.mergeCreativeAssistantHistoryRecord([
                {{ id: "old-duplicate-id", prompt: "旧记录", result: {{ title: "旧标题" }} }},
                {{ id: "same-signature", prompt: "写一个雨夜开场", result: {{ title: "雨夜秘密" }} }},
                {{ id: "keep-1", prompt: "保留一", result: {{ title: "标题一" }} }},
                {{ id: "keep-2", prompt: "保留二", result: {{ title: "标题二" }} }},
              ], record, 3),
              preservedFavorite: tools.mergeCreativeAssistantHistoryRecord([
                {{ ...record, id: "old-favorite", favorite: true }},
              ], {{ ...record, id: "new-version", favorite: false }}, 3)[0].favorite,
              cappedFavoriteIds: tools.capCreativeAssistantHistoryRecords([
                {{ id: "fresh", favorite: false }},
                {{ id: "recent", favorite: false }},
                {{ id: "old-favorite", favorite: true }},
                {{ id: "overflow", favorite: false }},
              ], 3).map((item) => item.id),
              mergedFavoriteIds: tools.mergeCreativeAssistantHistoryRecord([
                {{ id: "recent-a", prompt: "A", result: {{ title: "A" }}, favorite: false }},
                {{ id: "recent-b", prompt: "B", result: {{ title: "B" }}, favorite: false }},
                {{ id: "old-keeper", prompt: "K", result: {{ title: "K" }}, favorite: true }},
              ], {{ id: "new-top", prompt: "N", result: {{ title: "N" }}, favorite: false }}, 3).map((item) => item.id),
              zeroLimit: tools.mergeCreativeAssistantHistoryRecord([], record, 0),
              defaultMode: tools.getSafeCreativeAssistantMode("unknown"),
              scriptMode: tools.getSafeCreativeAssistantMode("script"),
              defaultProvider: tools.getSafeCreativeAssistantProvider("bad"),
              openaiProvider: tools.getSafeCreativeAssistantProvider("openai"),
              deepseekProvider: tools.getSafeCreativeAssistantProvider("deepseek"),
              providerConfig: tools.getCreativeAssistantProviderConfig("deepseek"),
              defaultModel: tools.getSafeCreativeAssistantModel("   "),
              deepseekDefaultModel: tools.getSafeCreativeAssistantModel("   ", "deepseek"),
              customBaseUrl: tools.getSafeCreativeAssistantBaseUrl("  http://127.0.0.1:11434/v1  "),
              defaultSettings: tools.getDefaultCreativeAssistantSettings(),
              activeIndexes: tools.getActiveCreativeAssistantBlockIndexes(record.result, [2, 0, 99, 0]),
              selectedTypes: tools.getSelectedCreativeAssistantBlocks(record.result, [1]).map((block) => block.type),
              dialoguePreview: tools.getCreativeAssistantBlockPreviewText(record.result.blocks[0], 0),
              choicePreview: tools.getCreativeAssistantBlockPreviewText(record.result.blocks[1], 1),
              selectedBlocksText: tools.buildCreativeAssistantBlocksText(record.result, [0, 2]),
              archive: tools.buildCreativeAssistantHistoryArchive([record, null], {{
                projectTitle: "  星夜测试项目  ",
                exportedAt: "2026-05-05T00:00:00.000Z",
                limit: 1,
              }}),
              recoverySnapshot: tools.buildCreativeAssistantHistoryRecoverySnapshot([record], {{
                createdAt: "2026-05-05T00:00:00.000Z",
                reason: "clear_all",
                limit: 1,
              }}),
              recoverySwap: tools.buildCreativeAssistantHistoryRecoverySwap(
                [{{ id: "current", prompt: "当前灵感", result: {{ title: "当前标题" }}, favorite: true }}],
                tools.buildCreativeAssistantHistoryRecoverySnapshot([record], {{
                  createdAt: "2026-05-05T00:00:00.000Z",
                  reason: "clear_nonfavorites",
                  limit: 1,
                }}),
                {{
                  createdAt: "2026-05-06T00:00:00.000Z",
                  reason: "before_restore",
                  limit: 3,
                }}
              ),
              emptyRecoverySwap: tools.buildCreativeAssistantHistoryRecoverySwap(
                [{{ id: "current", prompt: "当前灵感", result: {{ title: "当前标题" }} }}],
                null,
                {{ limit: 3 }}
              ),
              generationResult: tools.sanitizeCreativeAssistantGenerationResponse({{
                result: {{
                  ...record.result,
                  apiKey: "should-not-survive",
                  secretDebug: "should-not-survive",
                  provider: {{
                    mode: "openai",
                    model: "gpt-test",
                    fallback: false,
                    apiKey: "should-not-survive",
                  }},
                  privacy: {{
                    sentToExternalService: true,
                    message: "  已调用真模型  ",
                    apiKey: "should-not-survive",
                  }},
                  blocks: [
                    {{ type: "dialogue", text: "  安全清洗后的台词  ", speakerId: "heroine" }},
                    {{ type: "unsafe", text: "会转成旁白", extra: "drop" }},
                  ],
                }},
                apiKey: "should-not-survive",
              }}),
              invalidGenerationResult: tools.sanitizeCreativeAssistantGenerationResponse({{ result: null }}),
              importedArchiveIds: tools.getCreativeAssistantHistoryArchiveRecords({{
                records: [record],
              }}).map((item) => item.id),
              importedSingleIds: tools.getCreativeAssistantHistoryArchiveRecords({{
                record,
              }}).map((item) => item.id),
              filteredByTitle: tools.filterCreativeAssistantHistoryRecords([record], {{ query: "雨夜" }}).map((item) => item.id),
              filteredByBlock: tools.filterCreativeAssistantHistoryRecords([record], {{ query: "追上去" }}).map((item) => item.id),
              favoriteOnly: tools.filterCreativeAssistantHistoryRecords([record], {{ favoritesOnly: true }}).map((item) => item.id),
              favoriteOnlyEmpty: tools.filterCreativeAssistantHistoryRecords([
                {{ ...record, favorite: false }}
              ], {{ favoritesOnly: true }}).length,
              searchText: tools.getCreativeAssistantHistorySearchText(record),
              recordMarkdown: tools.buildCreativeAssistantRecordMarkdown(record, 0),
              historyMarkdown: tools.buildCreativeAssistantHistoryMarkdown([record], {{
                projectTitle: "星夜测试项目",
                exportedAt: "2026-05-05T00:00:00.000Z",
                query: "追上去",
              }}),
              trimmed: tools.trimCreativeAssistantText("  abcdef  ", 3),
              firstSample: tools.CREATIVE_ASSISTANT_PROMPT_SAMPLES[0],
              record,
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
        self.assertEqual([item["id"] for item in payload["merged"]], ["fixed_id", "old-duplicate-id", "keep-1"])
        self.assertTrue(payload["preservedFavorite"])
        self.assertEqual(payload["cappedFavoriteIds"], ["fresh", "recent", "old-favorite"])
        self.assertEqual(payload["mergedFavoriteIds"], ["new-top", "recent-a", "old-keeper"])
        self.assertEqual(payload["zeroLimit"], [])
        self.assertEqual(payload["defaultMode"], "starter_demo")
        self.assertEqual(payload["scriptMode"], "script")
        self.assertEqual(payload["defaultProvider"], "local")
        self.assertEqual(payload["openaiProvider"], "openai")
        self.assertEqual(payload["deepseekProvider"], "deepseek")
        self.assertEqual(payload["providerConfig"]["defaultModel"], "deepseek-v4-flash")
        self.assertEqual(payload["defaultModel"], "gpt-5.5")
        self.assertEqual(payload["deepseekDefaultModel"], "deepseek-v4-flash")
        self.assertEqual(payload["customBaseUrl"], "http://127.0.0.1:11434/v1")
        self.assertEqual(payload["defaultSettings"]["provider"], "local")
        self.assertFalse(payload["defaultSettings"]["rememberKey"])
        self.assertEqual(payload["defaultSettings"]["openAiKey"], "")
        self.assertEqual(payload["defaultSettings"]["apiKey"], "")
        self.assertEqual(payload["activeIndexes"], [0, 2])
        self.assertEqual(payload["selectedTypes"], ["choice"])
        self.assertIn("#1 台词", payload["dialoguePreview"])
        self.assertIn("【heroine】", payload["dialoguePreview"])
        self.assertIn("#2 选项", payload["choicePreview"])
        self.assertIn("1. 追上去", payload["choicePreview"])
        self.assertIn("《雨夜秘密》", payload["selectedBlocksText"])
        self.assertIn("#2 旁白", payload["selectedBlocksText"])
        self.assertEqual(payload["archive"]["engine"], "Canvasia Engine")
        self.assertEqual(payload["archive"]["kind"], "creative_assistant_history_archive")
        self.assertEqual(payload["archive"]["formatVersion"], 1)
        self.assertEqual(payload["archive"]["exportedAt"], "2026-05-05T00:00:00.000Z")
        self.assertEqual(payload["archive"]["projectTitle"], "星夜测试项目")
        self.assertEqual(payload["archive"]["recordCount"], 1)
        self.assertEqual(payload["archive"]["records"][0]["id"], "fixed_id")
        self.assertFalse(payload["archive"]["privacy"]["containsApiKey"])
        self.assertEqual(payload["recoverySnapshot"]["kind"], "creative_assistant_history_recovery")
        self.assertEqual(payload["recoverySnapshot"]["reason"], "clear_all")
        self.assertEqual(payload["recoverySnapshot"]["recordCount"], 1)
        self.assertFalse(payload["recoverySnapshot"]["privacy"]["containsApiKey"])
        self.assertTrue(payload["recoverySwap"]["canRestore"])
        self.assertEqual(payload["recoverySwap"]["currentRecordCount"], 1)
        self.assertEqual(payload["recoverySwap"]["restoredRecordCount"], 1)
        self.assertEqual(payload["recoverySwap"]["restoredRecords"][0]["id"], "fixed_id")
        self.assertEqual(payload["recoverySwap"]["nextRecoverySnapshot"]["reason"], "before_restore")
        self.assertEqual(payload["recoverySwap"]["nextRecoverySnapshot"]["recordCount"], 1)
        self.assertEqual(payload["recoverySwap"]["nextRecoverySnapshot"]["records"][0]["id"], "current")
        self.assertFalse(payload["recoverySwap"]["nextRecoverySnapshot"]["privacy"]["containsApiKey"])
        self.assertFalse(payload["emptyRecoverySwap"]["canRestore"])
        self.assertEqual(payload["emptyRecoverySwap"]["currentRecordCount"], 1)
        self.assertEqual(payload["emptyRecoverySwap"]["restoredRecords"], [])
        self.assertIsNone(payload["emptyRecoverySwap"]["nextRecoverySnapshot"])
        self.assertEqual(payload["generationResult"]["title"], "雨夜秘密")
        self.assertEqual(payload["generationResult"]["provider"]["mode"], "openai")
        self.assertEqual(payload["generationResult"]["provider"]["model"], "gpt-test")
        self.assertTrue(payload["generationResult"]["privacy"]["sentToExternalService"])
        self.assertEqual(payload["generationResult"]["blocks"][0]["text"], "安全清洗后的台词")
        self.assertEqual(payload["generationResult"]["blocks"][1]["type"], "narration")
        self.assertNotIn("apiKey", json.dumps(payload["generationResult"], ensure_ascii=False))
        self.assertNotIn("secretDebug", json.dumps(payload["generationResult"], ensure_ascii=False))
        self.assertIsNone(payload["invalidGenerationResult"])
        self.assertEqual(payload["importedArchiveIds"], ["fixed_id"])
        self.assertEqual(payload["importedSingleIds"], ["fixed_id"])
        self.assertEqual(payload["filteredByTitle"], ["fixed_id"])
        self.assertEqual(payload["filteredByBlock"], ["fixed_id"])
        self.assertEqual(payload["favoriteOnly"], ["fixed_id"])
        self.assertEqual(payload["favoriteOnlyEmpty"], 0)
        self.assertIn("雨夜秘密", payload["searchText"])
        self.assertIn("追上去", payload["searchText"])
        self.assertIn("## 1. 雨夜秘密", payload["recordMarkdown"])
        self.assertIn("★", payload["recordMarkdown"])
        self.assertIn("# 星夜测试项目 · Canvasia Assistant 灵感档案", payload["historyMarkdown"])
        self.assertIn("关键词：追上去", payload["historyMarkdown"])
        self.assertIn("隐私说明", payload["historyMarkdown"])
        self.assertIn("可插入剧情卡片", payload["historyMarkdown"])
        self.assertEqual(payload["trimmed"], "abc")
        self.assertIn("雨夜校园", payload["firstSample"])

        record = payload["record"]
        self.assertEqual(record["id"], "fixed_id")
        self.assertEqual(record["createdAt"], "2026-05-04T00:00:00.000Z")
        self.assertEqual(record["prompt"], "写一个雨夜开场")
        self.assertEqual(record["sceneName"], "当前场景")
        self.assertTrue(record["favorite"])
        self.assertEqual(record["result"]["mode"], "starter_demo")
        self.assertEqual(record["result"]["title"], "雨夜秘密")
        self.assertEqual(record["result"]["provider"]["mode"], "openai")
        self.assertEqual(record["result"]["provider"]["model"], "gpt-test")
        self.assertTrue(record["result"]["provider"]["fallback"])
        self.assertTrue(record["result"]["privacy"]["sentToExternalService"])
        self.assertEqual(record["result"]["blockCount"], 3)
        self.assertEqual(record["result"]["blocks"][0]["speakerId"], "heroine")
        self.assertEqual(record["result"]["blocks"][1]["type"], "choice")
        self.assertEqual(len(record["result"]["blocks"][1]["options"]), 4)
        self.assertEqual(record["result"]["blocks"][1]["options"][0]["effects"], [])
        self.assertEqual(record["result"]["blocks"][2]["type"], "narration")

    def test_creative_assistant_storage_helpers_keep_api_key_private_by_default(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorCreativeAssistant;
            const storage = {{
              values: new Map(),
              getItem(key) {{
                return this.values.has(key) ? this.values.get(key) : null;
              }},
              setItem(key, value) {{
                this.values.set(key, String(value));
              }},
              removeItem(key) {{
                this.values.delete(key);
              }},
            }};
            tools.persistCreativeAssistantSettings(storage, {{
              provider: "deepseek",
              model: " deepseek-custom ",
              baseUrl: " https://custom.example/v1 ",
              rememberKey: false,
              apiKey: "secret-key",
            }});
            const privateSettings = tools.loadCreativeAssistantSettings(storage);
            const keyAfterPrivateSave = storage.getItem(tools.CREATIVE_ASSISTANT_API_KEY_STORAGE_KEY);
            tools.persistCreativeAssistantSettings(storage, {{
              provider: "deepseek",
              model: "deepseek-custom",
              baseUrl: "https://custom.example/v1",
              rememberKey: true,
              apiKey: "secret-key",
            }});
            const rememberedSettings = tools.loadCreativeAssistantSettings(storage);
            tools.persistCreativeAssistantHistory(storage, [
              {{ id: "a", prompt: "one", result: {{ title: "One" }} }},
              {{ id: "b", prompt: "two", result: {{ title: "Two" }} }},
            ], 1);
            const savedHistory = JSON.parse(storage.getItem(tools.CREATIVE_ASSISTANT_HISTORY_STORAGE_KEY));
            const result = {{
              privateSettings,
              keyAfterPrivateSave,
              rememberedSettings,
              savedHistoryLength: savedHistory.length,
              savedHistoryFirstId: savedHistory[0].id,
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
        self.assertEqual(payload["privateSettings"]["provider"], "deepseek")
        self.assertEqual(payload["privateSettings"]["model"], "deepseek-custom")
        self.assertEqual(payload["privateSettings"]["baseUrl"], "https://custom.example/v1")
        self.assertFalse(payload["privateSettings"]["rememberKey"])
        self.assertEqual(payload["privateSettings"]["openAiKey"], "")
        self.assertEqual(payload["privateSettings"]["apiKey"], "")
        self.assertIsNone(payload["keyAfterPrivateSave"])
        self.assertTrue(payload["rememberedSettings"]["rememberKey"])
        self.assertEqual(payload["rememberedSettings"]["openAiKey"], "secret-key")
        self.assertEqual(payload["rememberedSettings"]["apiKey"], "secret-key")
        self.assertEqual(payload["savedHistoryLength"], 1)
        self.assertEqual(payload["savedHistoryFirstId"], "a")

    def test_editor_app_delegates_creative_assistant_privacy_logic_to_module(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("} = creativeAssistantTools;", app_source)
        self.assertNotIn("const CREATIVE_ASSISTANT_MODES = creativeAssistantTools?.CREATIVE_ASSISTANT_MODES", app_source)
        self.assertNotIn("CREATIVE_ASSISTANT_API_KEY_STORAGE_KEY", app_source)
        self.assertNotIn("creativeAssistantTools?.sanitizeCreativeAssistantHistoryResult", app_source)
        self.assertNotIn("creativeAssistantTools?.buildCreativeAssistantHistoryArchive", app_source)
        self.assertIn("return creativeAssistantTools.sanitizeCreativeAssistantHistoryResult(result);", app_source)
        self.assertIn("creativeAssistantTools.persistCreativeAssistantSettings(localStorage, {", app_source)
        self.assertIn("return creativeAssistantTools.filterCreativeAssistantHistoryRecords(records, options);", app_source)
        self.assertIn("const recoveryPlan = creativeAssistantTools.buildCreativeAssistantHistoryRecoverySwap(", app_source)


if __name__ == "__main__":
    unittest.main()
