from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "openai_asset_generator.js"


class FrontendOpenAiAssetGeneratorModuleTests(unittest.TestCase):
    def test_openai_asset_generator_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorOpenAiAssetGenerator;
            const fakeApiKey = ["sk", "test"].join("-");
            const state = {{
              ...tools.getDefaultOpenAiAssetGenerationState(),
              openAiAssetType: "sprite",
              openAiAssetPrompt: "原创女主角立绘",
              openAiAssetName: "女主默认",
              openAiAssetApiKey: fakeApiKey,
              openAiAssetModel: "gpt-image-test",
              openAiAssetStyleHint: "清透蓝白、柔和光线、校园恋爱氛围",
              openAiAssetBindCharacterId: "char_hero",
              openAiAssetBindExpressionId: "expr_smile",
              openAiAssetBindExpressionName: "微笑",
              openAiAssetBindAsDefaultSprite: true,
              openAiAssetSize: "1536x1024",
              openAiAssetQuality: "high",
              openAiAssetBackground: "transparent",
              openAiAssetOutputFormat: "webp",
              openAiAssetLastResult: {{
                asset: {{ name: "女主默认", type: "sprite", path: "assets/sprites/heroine.webp" }},
                privacy: {{
                  apiKeyStored: false,
                  message: "API Key 只随本次请求发送给 OpenAI，没有写入项目文件或素材元数据。",
                }},
              }},
            }};
            const html = tools.renderOpenAiAssetGeneratorPanel({{
              state,
              selectedAssetType: "background",
              characters: [
                {{ id: "char_hero", displayName: "女主角" }},
                {{ id: "char_friend", displayName: "好友" }},
              ],
              escapeHtml: (value) => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
              getAssetTypeLabel: (type) => ({{ background: "背景", sprite: "立绘", cg: "CG", ui: "界面素材" }}[type] || type),
            }});
            const loadingHtml = tools.renderOpenAiAssetGeneratorPanel({{
              state: {{ ...state, openAiAssetLoading: true }},
              selectedAssetType: "sprite",
              characters: [{{ id: "char_hero", displayName: "女主角" }}],
              escapeHtml: (value) => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
              getAssetTypeLabel: (type) => ({{ background: "背景", sprite: "立绘", cg: "CG", ui: "界面素材" }}[type] || type),
            }});
            const errorHtml = tools.renderOpenAiAssetGeneratorPanel({{
              state: {{ ...state, openAiAssetError: "生成失败：额度不足", openAiAssetLastResult: null }},
              selectedAssetType: "sprite",
              characters: [{{ id: "char_hero", displayName: "女主角" }}],
              escapeHtml: (value) => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
              getAssetTypeLabel: (type) => ({{ background: "背景", sprite: "立绘", cg: "CG", ui: "界面素材" }}[type] || type),
            }});
            const emptyKeyHtml = tools.renderOpenAiAssetGeneratorPanel({{
              state: {{ ...state, openAiAssetApiKey: "" }},
              selectedAssetType: "sprite",
              characters: [{{ id: "char_hero", displayName: "女主角" }}],
              escapeHtml: (value) => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
              getAssetTypeLabel: (type) => ({{ background: "背景", sprite: "立绘", cg: "CG", ui: "界面素材" }}[type] || type),
            }});
            const overlongPrompt = "长".repeat(tools.OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS + 1);
            const overlongStyleHint = "清".repeat(tools.OPENAI_ASSET_GENERATION_MAX_STYLE_HINT_CHARS + 1);
            const overlongHtml = tools.renderOpenAiAssetGeneratorPanel({{
              state: {{ ...state, openAiAssetPrompt: overlongPrompt, openAiAssetLastResult: null }},
              selectedAssetType: "sprite",
              characters: [{{ id: "char_hero", displayName: "女主角" }}],
              escapeHtml: (value) => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
              getAssetTypeLabel: (type) => ({{ background: "背景", sprite: "立绘", cg: "CG", ui: "界面素材" }}[type] || type),
            }});
            const overlongStyleHintHtml = tools.renderOpenAiAssetGeneratorPanel({{
              state: {{ ...state, openAiAssetStyleHint: overlongStyleHint, openAiAssetLastResult: null }},
              selectedAssetType: "sprite",
              characters: [{{ id: "char_hero", displayName: "女主角" }}],
              escapeHtml: (value) => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
              getAssetTypeLabel: (type) => ({{ background: "背景", sprite: "立绘", cg: "CG", ui: "界面素材" }}[type] || type),
            }});
            const invalidModelHtml = tools.renderOpenAiAssetGeneratorPanel({{
              state: {{ ...state, openAiAssetModel: "坏 model", openAiAssetLastResult: null }},
              selectedAssetType: "sprite",
              characters: [{{ id: "char_hero", displayName: "女主角" }}],
              escapeHtml: (value) => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
              getAssetTypeLabel: (type) => ({{ background: "背景", sprite: "立绘", cg: "CG", ui: "界面素材" }}[type] || type),
            }});
            const incompatibleState = {{
              ...state,
              openAiAssetBackground: "transparent",
              openAiAssetOutputFormat: "jpeg",
              openAiAssetLastResult: null,
            }};
            const incompatibleHtml = tools.renderOpenAiAssetGeneratorPanel({{
              state: incompatibleState,
              selectedAssetType: "sprite",
              characters: [{{ id: "char_hero", displayName: "女主角" }}],
              escapeHtml: (value) => String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"),
              getAssetTypeLabel: (type) => ({{ background: "背景", sprite: "立绘", cg: "CG", ui: "界面素材" }}[type] || type),
            }});
            function getButtonSnippet(source, action) {{
              const marker = `data-action="${{action}}"`;
              const index = source.indexOf(marker);
              return index >= 0 ? source.slice(Math.max(0, index - 180), index + 220) : "";
            }}
            const forgetKeyButton = getButtonSnippet(html, "forget-openai-asset-key");
            const emptyKeyButton = getButtonSnippet(emptyKeyHtml, "forget-openai-asset-key");
            const loadingForgetKeyButton = getButtonSnippet(loadingHtml, "forget-openai-asset-key");
            const result = {{
              api: tools.API_GENERATE_OPENAI_ASSET,
              defaultType: tools.getDefaultOpenAiAssetGenerationState().openAiAssetType,
              safeType: tools.getSafeOpenAiAssetGenerationType("bad"),
              safeOption: tools.getSafeOpenAiAssetGenerationOption("bad", tools.OPENAI_ASSET_GENERATION_SIZES, "1024x1024"),
              spritePrompt: tools.getOpenAiAssetPromptSample("sprite"),
              maxPromptChars: tools.OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS,
              maxStyleHintChars: tools.OPENAI_ASSET_GENERATION_MAX_STYLE_HINT_CHARS,
              stylePresetCount: tools.OPENAI_ASSET_GENERATION_STYLE_HINT_PRESETS.length,
              firstStylePreset: tools.getOpenAiAssetStyleHintPreset("clear-school"),
              missingStylePreset: tools.getOpenAiAssetStyleHintPreset("missing"),
              expressionPresetCount: tools.OPENAI_ASSET_EXPRESSION_BIND_PRESETS.length,
              smileExpressionPreset: tools.getOpenAiAssetExpressionBindPreset("expr_smile"),
              missingExpressionPreset: tools.getOpenAiAssetExpressionBindPreset("missing"),
              promptLength: tools.getOpenAiAssetPromptLengthInfo(state.openAiAssetPrompt).length,
              promptLengthLabel: tools.getOpenAiAssetPromptLengthLabel(state.openAiAssetPrompt),
              overlongPromptWarning: tools.getOpenAiAssetPromptLengthWarning(overlongPrompt),
              styleHintLengthLabel: tools.getOpenAiAssetStyleHintLengthLabel(state.openAiAssetStyleHint),
              overlongStyleHintWarning: tools.getOpenAiAssetStyleHintLengthWarning(overlongStyleHint),
              hasPromptMaxLength: html.includes('id="openAiAssetPrompt" maxlength="1400"'),
              hasPromptLengthStatus: html.includes('id="openAiAssetPromptLengthStatus"') && html.includes("提示词 7 / 1400 字"),
              hasOverlongPromptWarning: overlongHtml.includes("提示词超过 1400 字，请缩短后再生成。"),
              invalidModelWarning: tools.getOpenAiAssetModelWarning("坏 model"),
              emptyModelWarning: tools.getOpenAiAssetModelWarning(""),
              hasModelHelper: html.includes("留空会使用默认模型；自定义模型名不要包含空格。"),
              hasInvalidModelWarning: invalidModelHtml.includes("模型名只能包含英文字母、数字、点、下划线、冒号或短横线"),
              hasStyleHintField: html.includes('id="openAiAssetStyleHint"') && html.includes('maxlength="260"'),
              hasStyleHintLengthStatus: html.includes('id="openAiAssetStyleHintLengthStatus"') && html.includes("画风补充 16 / 260 字"),
              hasOverlongStyleHintWarning: overlongStyleHintHtml.includes("画风补充超过 260 字，请缩短后再生成。"),
              hasStylePresetButtons: html.includes('data-action="apply-openai-asset-style-preset"') && html.includes("清透校园"),
              hasActiveStylePreset: html.includes('openai-asset-style-preset is-active'),
              hasLockedStylePreset: loadingHtml.includes('data-action="apply-openai-asset-style-preset"') && loadingHtml.includes('title="AI 素材正在生成，请稍等..."'),
              hasCharacterBindPanel: html.includes("生成后绑定角色") && html.includes('id="openAiAssetBindCharacterId"'),
              hasCharacterOption: html.includes("女主角") && html.includes("好友"),
              hasExpressionPreset: html.includes('data-action="apply-openai-asset-expression-preset"') && html.includes("微笑"),
              hasDefaultSpriteToggle: html.includes('id="openAiAssetBindAsDefaultSprite"') && html.includes("同时设为角色默认立绘"),
              hasLockedCharacterBind: loadingHtml.includes('id="openAiAssetBindCharacterId"') && loadingHtml.includes('title="AI 素材正在生成，请稍等..."'),
              compatibilityWarning: tools.getOpenAiAssetGenerationCompatibilityWarning(incompatibleState),
              noCompatibilityWarning: tools.getOpenAiAssetGenerationCompatibilityWarning(state),
              payload: tools.buildOpenAiAssetGenerationPayload(state),
              hasButton: html.includes('data-action="generate-openai-asset"'),
              hasPrivacyCopy: html.includes("不会写入项目文件"),
              hasLastResult: html.includes("女主默认"),
              hasLastResultStatus: html.includes('class="helper-text good-text" role="status" aria-live="polite"'),
              hasLastResultPath: html.includes("保存位置：assets/sprites/heroine.webp"),
              hasLastResultPrivacyNote: html.includes("隐私确认：API Key 只随本次请求发送给 OpenAI，没有写入项目文件或素材元数据。"),
              hasCompatibilityWarning: incompatibleHtml.includes('class="helper-text warn-text" role="note"') && incompatibleHtml.includes("JPEG 不支持透明背景"),
              hasLoadingLabel: loadingHtml.includes("正在生成..."),
              hasLoadingBusyClass: loadingHtml.includes("is-busy"),
              hasLoadingAriaBusy: loadingHtml.includes('aria-busy="true"'),
              hasLoadingAriaDisabled: loadingHtml.includes('aria-disabled="true"'),
              hasLoadingLiveStatus: loadingHtml.includes('role="status" aria-live="polite"'),
              hasLoadingImportCopy: loadingHtml.includes("完成后会自动导入素材库"),
              hasSampleLocked: loadingHtml.includes("is-locked"),
              hasSampleDisabled: loadingHtml.includes('data-action="apply-openai-asset-prompt-sample"') && loadingHtml.includes('aria-disabled="true"'),
              hasSampleLockTitle: loadingHtml.includes('title="AI 素材正在生成，请稍等..."'),
              hasForgetKeyButton: html.includes('data-action="forget-openai-asset-key"'),
              forgetKeyButtonEnabled: forgetKeyButton && !forgetKeyButton.includes("disabled"),
              hasForgetKeyTitle: forgetKeyButton.includes("只清空当前页面里的生图 Key，不影响项目文件"),
              emptyKeyButtonDisabled: emptyKeyButton.includes('disabled aria-disabled="true"'),
              loadingForgetKeyButtonLocked: loadingForgetKeyButton.includes("is-locked") && loadingForgetKeyButton.includes('disabled aria-disabled="true"'),
              lockedFieldCount: loadingHtml.split('disabled aria-disabled="true" title="AI 素材正在生成，请稍等..."').length - 1,
              hasLockedPrompt: loadingHtml.includes('id="openAiAssetPrompt"') && loadingHtml.includes('title="AI 素材正在生成，请稍等..."'),
              hasLockedApiKey: loadingHtml.includes('id="openAiAssetApiKey"') && loadingHtml.includes('title="AI 素材正在生成，请稍等..."'),
              hasLockedStyleHint: loadingHtml.includes('id="openAiAssetStyleHint"') && loadingHtml.includes('title="AI 素材正在生成，请稍等..."'),
              hasErrorAlert: errorHtml.includes('class="helper-text danger-text" role="alert"') && errorHtml.includes("生成失败：额度不足"),
            }};
            console.log(JSON.stringify(result));
            """
        )
        completed = subprocess.run(["node", "-e", script], text=True, capture_output=True, check=True)
        result = json.loads(completed.stdout)

        self.assertEqual(result["api"], "/api/generate-openai-asset")
        self.assertEqual(result["defaultType"], "background")
        self.assertEqual(result["safeType"], "background")
        self.assertEqual(result["safeOption"], "1024x1024")
        self.assertIn("立绘", result["spritePrompt"])
        self.assertEqual(result["maxPromptChars"], 1400)
        self.assertEqual(result["maxStyleHintChars"], 260)
        self.assertGreaterEqual(result["stylePresetCount"], 4)
        self.assertEqual(result["firstStylePreset"]["label"], "清透校园")
        self.assertIsNone(result["missingStylePreset"])
        self.assertGreaterEqual(result["expressionPresetCount"], 3)
        self.assertEqual(result["smileExpressionPreset"]["name"], "微笑")
        self.assertIsNone(result["missingExpressionPreset"])
        self.assertEqual(result["promptLength"], 7)
        self.assertEqual(result["promptLengthLabel"], "提示词 7 / 1400 字")
        self.assertIn("提示词超过 1400 字", result["overlongPromptWarning"])
        self.assertEqual(result["styleHintLengthLabel"], "画风补充 16 / 260 字")
        self.assertIn("画风补充超过 260 字", result["overlongStyleHintWarning"])
        self.assertTrue(result["hasPromptMaxLength"])
        self.assertTrue(result["hasPromptLengthStatus"])
        self.assertTrue(result["hasOverlongPromptWarning"])
        self.assertIn("模型名只能包含英文字母", result["invalidModelWarning"])
        self.assertEqual(result["emptyModelWarning"], "")
        self.assertTrue(result["hasModelHelper"])
        self.assertTrue(result["hasInvalidModelWarning"])
        self.assertTrue(result["hasStyleHintField"])
        self.assertTrue(result["hasStyleHintLengthStatus"])
        self.assertTrue(result["hasOverlongStyleHintWarning"])
        self.assertTrue(result["hasStylePresetButtons"])
        self.assertTrue(result["hasActiveStylePreset"])
        self.assertTrue(result["hasLockedStylePreset"])
        self.assertTrue(result["hasCharacterBindPanel"])
        self.assertTrue(result["hasCharacterOption"])
        self.assertTrue(result["hasExpressionPreset"])
        self.assertTrue(result["hasDefaultSpriteToggle"])
        self.assertTrue(result["hasLockedCharacterBind"])
        self.assertIn("JPEG 不支持透明背景", result["compatibilityWarning"])
        self.assertEqual(result["noCompatibilityWarning"], "")
        self.assertEqual(result["payload"]["assetType"], "sprite")
        self.assertEqual(result["payload"]["apiKey"], "sk-test")
        self.assertEqual(result["payload"]["styleHint"], "清透蓝白、柔和光线、校园恋爱氛围")
        self.assertEqual(result["payload"]["characterBinding"]["characterId"], "char_hero")
        self.assertEqual(result["payload"]["characterBinding"]["expressionId"], "expr_smile")
        self.assertEqual(result["payload"]["characterBinding"]["expressionName"], "微笑")
        self.assertTrue(result["payload"]["characterBinding"]["setAsDefaultSprite"])
        self.assertEqual(result["payload"]["outputFormat"], "webp")
        self.assertTrue(result["hasButton"])
        self.assertTrue(result["hasPrivacyCopy"])
        self.assertTrue(result["hasLastResult"])
        self.assertTrue(result["hasLastResultStatus"])
        self.assertTrue(result["hasLastResultPath"])
        self.assertTrue(result["hasLastResultPrivacyNote"])
        self.assertTrue(result["hasCompatibilityWarning"])
        self.assertTrue(result["hasLoadingLabel"])
        self.assertTrue(result["hasLoadingBusyClass"])
        self.assertTrue(result["hasLoadingAriaBusy"])
        self.assertTrue(result["hasLoadingAriaDisabled"])
        self.assertTrue(result["hasLoadingLiveStatus"])
        self.assertTrue(result["hasLoadingImportCopy"])
        self.assertTrue(result["hasSampleLocked"])
        self.assertTrue(result["hasSampleDisabled"])
        self.assertTrue(result["hasSampleLockTitle"])
        self.assertTrue(result["hasForgetKeyButton"])
        self.assertTrue(result["forgetKeyButtonEnabled"])
        self.assertTrue(result["hasForgetKeyTitle"])
        self.assertTrue(result["emptyKeyButtonDisabled"])
        self.assertTrue(result["loadingForgetKeyButtonLocked"])
        self.assertGreaterEqual(result["lockedFieldCount"], 13)
        self.assertTrue(result["hasLockedPrompt"])
        self.assertTrue(result["hasLockedApiKey"])
        self.assertTrue(result["hasLockedStyleHint"])
        self.assertTrue(result["hasErrorAlert"])


if __name__ == "__main__":
    unittest.main()
