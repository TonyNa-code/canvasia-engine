from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "story_block_editors.js"


class FrontendStoryBlockEditorsModuleTests(unittest.TestCase):
    def test_choice_editor_renderers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorStoryBlockEditors;
            const blockManagementMarkup = tools.renderBlockManagementCard(
              {{ name: "第一场 <黄昏>", blocks: [{{ id: "b1" }}, {{ id: "b2" }}, {{ id: "b3" }}] }},
              1,
              {{
                renderDetailRows: (rows) => `<dl>${{rows.map((row) => `<dt>${{row[0]}}</dt><dd>${{row[1]}}</dd>`).join("")}}</dl>`,
              }}
            );
            const firstBlockManagementMarkup = tools.renderBlockManagementCard(
              {{ name: "第一场", blocks: [{{ id: "b1" }}] }},
              0,
              {{
                renderDetailRows: () => "",
              }}
            );
            const readonlyMarkup = tools.renderReadonlyBlockPanel(
              {{ type: "custom_block", id: "legacy_1" }},
              {{
                buildBlockDetails: (block) => [["卡片类型", block.type], ["卡片 ID", block.id]],
                renderDetailRows: (rows) => `<dl>${{rows.map((row) => `<dt>${{row[0]}}</dt><dd>${{row[1]}}</dd>`).join("")}}</dl>`,
              }}
            );
            const effectMarkup = tools.renderChoiceEffectEditorRow(
              {{ type: "variable_add", variableId: "score", value: 2 }},
              1,
              3,
              {{
                normalizeChoiceEffect: (effect) => effect,
                renderChoiceEffectTypeOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderVariableOptions: (selected, filter) => `<option value="${{selected}}" data-filter="${{filter}}">${{selected}}</option>`,
                renderChoiceEffectValueFields: (type, variableId, value) => `<input data-field="value" value="${{type}}:${{variableId}}:${{value}}" />`,
              }}
            );
            const optionMarkup = tools.renderChoiceOptionEditorRow(
              {{
                id: "opt\\"1",
                text: "一起 <回家>",
                gotoSceneId: "scene_b",
                effects: [
                  {{ type: "variable_add", variableId: "score", value: 2 }},
                  {{ type: "legacy_effect", value: "keep" }},
                ],
              }},
              0,
              2,
              {{
                scenes: [
                  {{ id: "scene_a", name: "开头" }},
                  {{ id: "scene_b", name: "结尾 & 真相" }},
                ],
                getEditableChoiceEffects: (effects) => effects.filter((effect) => effect.type === "variable_add"),
                renderChoiceTextQualityTools: (text) => `<small data-choice-text-tools>${{text.length}}</small>`,
                renderChoiceEffectEditorRow: (effect, index, count) => `<div data-rendered-effect="${{index}}/${{count}}">${{effect.variableId}}</div>`,
              }}
            );
            const ruleMarkup = tools.renderConditionRuleEditorRow(
              {{ variableId: "score", operator: ">=", value: 5 }},
              1,
              2,
              {{
                getSafeVariableId: (variableId) => variableId || "score",
                getSafeConditionOperator: (_variableId, operator) => operator || "==",
                renderVariableOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderConditionOperatorOptions: (_variableId, selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderConditionValueFields: (variableId, value) => `<input data-field="condition-value" value="${{variableId}}:${{value}}" />`,
              }}
            );
            const branchMarkup = tools.renderConditionBranchEditorRow(
              {{
                id: "branch\\"1",
                gotoSceneId: "scene_b",
                when: [{{ variableId: "score", operator: ">=", value: 5 }}],
              }},
              0,
              2,
              {{
                getSafeSceneId: (sceneId) => sceneId || "scene_a",
                getDefaultJumpTargetSceneId: () => "scene_a",
                renderSceneOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderConditionRuleEditorRow: (rule, index, count) => `<div data-rendered-rule="${{index}}/${{count}}">${{rule.variableId}}</div>`,
              }}
            );
            const conditionMarkup = tools.renderConditionEditor(
              {{
                id: "condition_1",
                branches: [
                  {{ id: "branch_1", gotoSceneId: "scene_b", when: [{{ variableId: "score", operator: ">=", value: 5 }}] }},
                ],
                elseGotoSceneId: "scene_c",
              }},
              {{
                selectedSceneId: "scene_a",
                createDefaultConditionBranches: () => [{{ id: "branch_default", gotoSceneId: "scene_b", when: [] }}],
                getSafeSceneId: (sceneId, fallback) => sceneId || fallback,
                getDefaultJumpTargetSceneId: () => "scene_b",
                getSceneLabelById: (sceneId) => ({{ scene_b: "真结局", scene_c: "普通结局" }}[sceneId] || sceneId),
                renderDetailRows: (rows) => `<dl>${{rows.map((row) => `<dt>${{row[0]}}</dt><dd>${{row[1]}}</dd>`).join("")}}</dl>`,
                renderSceneOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderConditionBranchEditorRow: (branch, index, count) => `<section data-condition-branch-row="${{index}}/${{count}}">${{branch.id}}</section>`,
              }}
            );
            const jumpMarkup = tools.renderJumpEditor(
              {{ targetSceneId: "scene_b" }},
              {{
                getSafeSceneId: (sceneId) => sceneId || "scene_a",
                renderSceneOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
              }}
            );
            const starterMarkup = tools.renderVariableStarterPrompt(
              "还没有 <变量>",
              "先创建 & 再继续",
            );
            const variableSetMarkup = tools.renderVariableSetEditor(
              {{ variableId: "route", value: "common" }},
              {{
                getSafeVariableId: (variableId) => variableId || "route",
                getVariableType: () => "string",
                getVariableTypeLabel: () => "文本 <路线>",
                renderVariableOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderVariableSetValueFields: (variableId, value) => `<input data-field="variable-value" value="${{variableId}}:${{value}}" />`,
              }}
            );
            const variableAddMarkup = tools.renderVariableAddEditor(
              {{ variableId: "score", value: "3.5" }},
              {{
                getSafeVariableId: (variableId) => variableId || "score",
                getSafeNumber: (value, fallback) => Number.parseFloat(value || fallback),
                renderVariableOptions: (selected, filter) => `<option value="${{selected}}" data-filter="${{filter}}" selected>${{selected}}</option>`,
              }}
            );
            const shakeMarkup = tools.renderScreenShakeEditor(
              {{ intensity: "heavy", duration: "long" }},
              {{
                shakeIntensityLabels: {{ medium: "明显", heavy: "很强" }},
                effectDurationLabels: {{ medium: "正常", long: "久一点" }},
                getSafeShakeIntensity: (value) => value || "medium",
                getSafeEffectDuration: (value) => value || "medium",
              }}
            );
            const flashMarkup = tools.renderScreenFlashEditor(
              {{ color: "red", intensity: "strong", duration: "short" }},
              {{
                flashColorLabels: {{ white: "白闪", red: "红闪" }},
                flashIntensityLabels: {{ medium: "明显", strong: "很亮" }},
                effectDurationLabels: {{ short: "短一下", medium: "正常" }},
                getSafeFlashColor: (value) => value || "white",
                getSafeFlashIntensity: (value) => value || "medium",
                getSafeEffectDuration: (value) => value || "medium",
              }}
            );
            const fadeMarkup = tools.renderScreenFadeEditor(
              {{ action: "fade_in", color: "white", duration: "long" }},
              {{
                fadeActionLabels: {{ fade_out: "慢慢淡出", fade_in: "慢慢亮起" }},
                fadeColorLabels: {{ black: "黑场", white: "白场" }},
                effectDurationLabels: {{ medium: "正常", long: "久一点" }},
                getSafeFadeAction: (value) => value || "fade_out",
                getSafeFadeColor: (value) => value || "black",
                getSafeEffectDuration: (value) => value || "medium",
              }}
            );
            const zoomMarkup = tools.renderCameraZoomEditor(
              {{ action: "zoom_out", strength: "heavy", focus: "right" }},
              {{
                cameraZoomActionLabels: {{ zoom_in: "推近镜头", zoom_out: "拉远镜头" }},
                cameraZoomStrengthLabels: {{ medium: "明显", heavy: "更强" }},
                cameraZoomFocusLabels: {{ center: "看中间", right: "看右侧" }},
                getSafeCameraZoomAction: (value) => value || "zoom_in",
                getSafeCameraZoomStrength: (value) => value || "medium",
                getSafeCameraZoomFocus: (value) => value || "center",
              }}
            );
            const panMarkup = tools.renderCameraPanEditor(
              {{ target: "left", strength: "light" }},
              {{
                cameraPanTargetLabels: {{ left: "向左看", center: "回到中间" }},
                cameraPanStrengthLabels: {{ light: "轻一点", medium: "明显" }},
                getSafeCameraPanTarget: (value) => value || "center",
                getSafeCameraPanStrength: (value) => value || "medium",
              }}
            );
            const filterMarkup = tools.renderScreenFilterEditor(
              {{ action: "apply", preset: "dream", strength: "strong", grade: {{ brightness: 123, hue: -12 }} }},
              {{
                screenFilterActionLabels: {{ apply: "开启滤镜", clear: "关闭滤镜" }},
                screenFilterPresetLabels: {{ memory: "暖色回忆", dream: "梦境柔光" }},
                screenFilterStrengthLabels: {{ medium: "正常", strong: "更明显" }},
                screenColorGradeDefaults: {{ brightness: 100, contrast: 100, saturation: 100, hue: 0, temperature: 0, vignette: 0 }},
                screenColorGradeLimits: {{ brightness: [40, 180], contrast: [40, 180], saturation: [0, 220], hue: [-180, 180], temperature: [-100, 100], vignette: [0, 100] }},
                getSafeScreenFilterAction: (value) => value || "apply",
                getSafeScreenFilterPreset: (value) => value || "memory",
                getSafeScreenFilterStrength: (value) => value || "medium",
                getSafeScreenColorGrade: (grade) => ({{ brightness: 123, contrast: 100, saturation: 100, hue: -12, temperature: 0, vignette: 0, ...grade }}),
              }}
            );
            const blurMarkup = tools.renderDepthBlurEditor(
              {{ action: "apply", focus: "full", strength: "strong" }},
              {{
                depthBlurActionLabels: {{ apply: "开启景深", clear: "关闭景深" }},
                depthBlurFocusLabels: {{ center: "中间角色更清楚", full: "只虚化背景" }},
                depthBlurStrengthLabels: {{ medium: "正常", strong: "更明显" }},
                getSafeDepthBlurAction: (value) => value || "apply",
                getSafeDepthBlurFocus: (value) => value || "center",
                getSafeDepthBlurStrength: (value) => value || "medium",
              }}
            );
            const readableMarkup = tools.renderReadableTextQualityTools(
              "很长的一句话",
              "台词",
              {{
                getReadableTextToolState: () => ({{
                  canSplit: true,
                  isLong: true,
                  metrics: {{ length: 12 }},
                  statusText: "建议拆分",
                  toneClass: "warn-text",
                }}),
                buildReadableTextSummary: (metrics) => `长度 ${{metrics.length}}`,
              }}
            );
            const dialogueMarkup = tools.renderDialogueEditor(
              {{ id: "block_1", speakerId: "char_a", expressionId: "smile", text: "你好 <世界>" }},
              {{
                selectedSceneId: "scene_a",
                characters: [
                  {{ id: "char_a", displayName: "女主 & A" }},
                  {{ id: "char_b", displayName: "男主" }},
                ],
                voiceAssets: [
                  {{ id: "voice_1", name: "第一句语音" }},
                ],
                assetsById: new Map(),
                getSafeCharacterId: (value) => value || "char_a",
                getSafeExpressionId: (_characterId, value) => value || "default",
                renderExpressionOptions: (characterId, expressionId) => `<option value="${{expressionId}}" selected>${{characterId}}:${{expressionId}}</option>`,
                renderReadableTextQualityTools: (text, label) => `<small data-readable>${{label}}:${{text}}</small>`,
              }}
            );
            const boundDialogueMarkup = tools.renderDialogueEditor(
              {{ id: "block_2", speakerId: "char_a", expressionId: "smile", voiceAssetId: "voice_1", text: "有语音" }},
              {{
                selectedSceneId: "scene_a",
                characters: [{{ id: "char_a", displayName: "女主" }}],
                voiceAssets: [{{ id: "voice_1", name: "第一句语音" }}],
                assetsById: new Map([["voice_1", {{ name: "第一句语音" }}]]),
                getSafeCharacterId: (value) => value || "char_a",
                getSafeExpressionId: (_characterId, value) => value || "default",
                renderExpressionOptions: (characterId, expressionId) => `<option value="${{expressionId}}" selected>${{characterId}}:${{expressionId}}</option>`,
                renderReadableTextQualityTools: () => "",
              }}
            );
            const choiceMarkup = tools.renderChoiceEditor(
              {{ id: "choice_1", type: "choice" }},
              {{
                blockLabels: {{ choice: "选项" }},
                createDefaultChoiceOptions: () => [
                  {{ id: "choice_1_option_1", text: "去天台", gotoSceneId: "scene_b", effects: [] }},
                ],
                renderDetailRows: (rows) => `<dl>${{rows.map((row) => `<dt>${{row[0]}}</dt><dd>${{row[1]}}</dd>`).join("")}}</dl>`,
                renderChoiceCountQualityTools: (count) => `<div data-choice-count="${{count}}"></div>`,
                renderChoiceOptionEditorRow: (option, index, count) => `<div data-choice-row="${{index}}/${{count}}">${{option.text}}</div>`,
              }}
            );
            const choiceCountMarkup = tools.renderChoiceCountQualityTools(
              5,
              {{
                choiceManyOptionsThreshold: 4,
                buildChoiceCountSummary: (count) => `当前有 ${{count}} 个选项 <偏多>`,
              }}
            );
            const narrationMarkup = tools.renderNarrationEditor(
              {{ text: "旁白 <内容>" }},
              {{
                renderReadableTextQualityTools: (text, label) => `<small data-readable>${{label}}:${{text}}</small>`,
              }}
            );
            const backgroundMarkup = tools.renderBackgroundEditor(
              {{
                assetId: "scene_3d",
                transition: "crossfade",
                scene3dPreview: {{ yaw: 45, pitch: 38, zoom: 1.25, interactionEnabled: false }},
              }},
              {{
                backgroundAssets: [
                  {{ id: "bg_1", name: "教室 <黄昏>", type: "background" }},
                  {{ id: "scene_3d", name: "天台 3D", type: "scene3d" }},
                ],
                getSafeTransition: (value) => value || "fade",
                getSafeScene3dPreviewConfig: (preview) => preview,
                renderTransitionOptions: (selected, optionBag) => `<option value="${{selected}}" data-basic="${{Boolean(optionBag?.basic)}}" selected>${{selected}}</option>`,
              }}
            );
            const characterShowMarkup = tools.renderCharacterShowEditor(
              {{ characterId: "char_a", expressionId: "smile", position: "right", transition: "slide" }},
              {{
                getSafeCharacterId: (value) => value || "char_a",
                getSafeExpressionId: (_characterId, value) => value || "default",
                getSafePosition: (value) => value || "center",
                getSafeTransition: (value) => value || "fade",
                getCharacterStageFromBlock: () => ({{ x: 12, scale: 1.2 }}),
                renderCharacterOptions: (selected) => `<option value="${{selected}}" selected>角色 ${{selected}}</option>`,
                renderExpressionOptions: (characterId, expressionId) => `<option value="${{expressionId}}" selected>${{characterId}}:${{expressionId}}</option>`,
                renderPositionOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderTransitionOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderCharacterStageControls: (stage) => `<section data-stage-x="${{stage.x}}" data-stage-scale="${{stage.scale}}">stage controls</section>`,
              }}
            );
            const characterHideMarkup = tools.renderCharacterHideEditor(
              {{ characterId: "char_a", transition: "fade" }},
              {{
                getSafeCharacterId: (value) => value || "char_a",
                getSafeTransition: (value) => value || "fade",
                renderCharacterOptions: (selected) => `<option value="${{selected}}" selected>角色 ${{selected}}</option>`,
                renderTransitionOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
              }}
            );
            const musicMarkup = tools.renderMusicPlayEditor(
              {{ assetId: "bgm_1", loop: false, endMode: "after_block", endBlockId: "block_9", fadeInMs: 800, fadeOutMs: 1200 }},
              {{
                musicAssets: [
                  {{ id: "bgm_1", name: "黄昏 BGM" }},
                  {{ id: "bgm_2", name: "夜晚 BGM" }},
                ],
                hasRangeCandidates: true,
                getSafeAssetIdByType: (_type, assetId) => assetId || "bgm_1",
                getSafeMusicEndMode: (mode) => mode || "until_next_music",
                renderMusicEndModeOptions: (selected) => `<option value="${{selected}}" selected>${{selected}}</option>`,
                renderMusicRangeEndBlockOptions: (block) => `<option value="${{block.endBlockId}}" selected>结束卡片</option>`,
              }}
            );
            const musicStopMarkup = tools.renderMusicStopEditor({{ fadeOutMs: 500 }});
            const sfxMarkup = tools.renderSfxPlayEditor(
              {{ assetId: "sfx_1" }},
              {{
                sfxAssets: [{{ id: "sfx_1", name: "门铃" }}],
                getSafeAssetIdByType: (_type, assetId) => assetId || "sfx_1",
              }}
            );
            const videoMarkup = tools.renderVideoPlayEditor(
              {{ assetId: "video_1", title: "OP <Movie>", fit: "cover", volume: 75, startTimeSeconds: 1.5, endTimeSeconds: 12, skippable: false }},
              {{
                videoAssets: [{{ id: "video_1", name: "开场动画" }}],
                videoFitLabels: {{ contain: "完整显示", cover: "铺满裁切" }},
                videoVolumeLabels: {{ 50: "50%", 75: "75%" }},
                getSafeAssetIdByType: (_type, assetId) => assetId || "video_1",
                getSafeNonNegativeNumber: (value, fallback) => Number.parseFloat(value ?? fallback),
                getSafeVideoVolume: (value) => Number(value ?? 100),
                getSafeVideoFit: (value) => value || "contain",
              }}
            );
            const creditsMarkup = tools.renderCreditsRollEditor(
              {{ title: "STAFF <END>", subtitle: "Thanks & Love", lines: ["企划：A", "音乐：B"], durationSeconds: 24, background: "light", skippable: false }},
              {{
                creditsBackgroundLabels: {{ dark: "深色电影片尾", light: "浅色清爽片尾" }},
                getCreditsLinesText: (lines) => lines.join("\\n"),
                getSafeCreditsDuration: (value) => value || 18,
                getSafeCreditsBackground: (value) => value || "dark",
              }}
            );
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              blockManagementMarkup,
              firstBlockManagementMarkup,
              readonlyMarkup,
              effectMarkup,
              emptyMarkup: tools.renderChoiceEffectEmptyState(),
              optionMarkup,
              ruleMarkup,
              branchMarkup,
              conditionMarkup,
              jumpMarkup,
              starterMarkup,
              variableSetMarkup,
              variableAddMarkup,
              shakeMarkup,
              flashMarkup,
              fadeMarkup,
              zoomMarkup,
              panMarkup,
              filterMarkup,
              blurMarkup,
              readableMarkup,
              dialogueMarkup,
              boundDialogueMarkup,
              choiceMarkup,
              choiceCountMarkup,
              narrationMarkup,
              backgroundMarkup,
              characterShowMarkup,
              characterHideMarkup,
              musicMarkup,
              musicStopMarkup,
              sfxMarkup,
              videoMarkup,
              creditsMarkup,
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
        self.assertEqual(payload["keys"], [
            "renderBackgroundEditor",
            "renderBlockManagementCard",
            "renderCameraPanEditor",
            "renderCameraZoomEditor",
            "renderCharacterHideEditor",
            "renderCharacterShowEditor",
            "renderChoiceCountQualityTools",
            "renderChoiceEditor",
            "renderChoiceEffectEditorRow",
            "renderChoiceEffectEmptyState",
            "renderChoiceOptionEditorRow",
            "renderColorGradeNumberInput",
            "renderConditionBranchEditorRow",
            "renderConditionEditor",
            "renderConditionRuleEditorRow",
            "renderCreditsRollEditor",
            "renderDepthBlurEditor",
            "renderDialogueEditor",
            "renderJumpEditor",
            "renderMusicPlayEditor",
            "renderMusicStopEditor",
            "renderNarrationEditor",
            "renderReadableTextQualityTools",
            "renderReadonlyBlockPanel",
            "renderScreenFadeEditor",
            "renderScreenFilterEditor",
            "renderScreenFlashEditor",
            "renderScreenShakeEditor",
            "renderSfxPlayEditor",
            "renderVariableAddEditor",
            "renderVariableSetEditor",
            "renderVariableStarterPrompt",
            "renderVideoPlayEditor",
        ])
        self.assertIn("管理这张卡片", payload["blockManagementMarkup"])
        self.assertIn("<dt>所在场景</dt><dd>第一场 <黄昏></dd>", payload["blockManagementMarkup"])
        self.assertIn("<dt>当前顺序</dt><dd>第 2 张 / 共 3 张</dd>", payload["blockManagementMarkup"])
        self.assertIn('data-action="move-block-up"', payload["blockManagementMarkup"])
        self.assertNotIn('data-action="move-block-up" disabled', payload["blockManagementMarkup"])
        self.assertIn('data-action="move-block-down"', payload["blockManagementMarkup"])
        self.assertNotIn('data-action="move-block-down"\n          disabled', payload["blockManagementMarkup"])
        self.assertIn('data-action="duplicate-block"', payload["blockManagementMarkup"])
        self.assertIn('data-action="delete-block"', payload["blockManagementMarkup"])
        self.assertIn('data-action="move-block-up" disabled', payload["firstBlockManagementMarkup"])
        self.assertIn('data-action="move-block-down"\n          disabled', payload["firstBlockManagementMarkup"])
        self.assertIn("高级兼容卡片", payload["readonlyMarkup"])
        self.assertIn("<dt>卡片类型</dt><dd>custom_block</dd>", payload["readonlyMarkup"])
        self.assertIn("<dt>卡片 ID</dt><dd>legacy_1</dd>", payload["readonlyMarkup"])
        self.assertIn("编辑屏幕震动", payload["shakeMarkup"])
        self.assertIn('value="heavy" selected', payload["shakeMarkup"])
        self.assertIn("编辑闪屏", payload["flashMarkup"])
        self.assertIn('value="red" selected', payload["flashMarkup"])
        self.assertIn("编辑黑场淡入淡出", payload["fadeMarkup"])
        self.assertIn('value="fade_in" selected', payload["fadeMarkup"])
        self.assertIn("编辑镜头推近拉远", payload["zoomMarkup"])
        self.assertIn('value="zoom_out" selected', payload["zoomMarkup"])
        self.assertIn("编辑镜头平移", payload["panMarkup"])
        self.assertIn('value="left" selected', payload["panMarkup"])
        self.assertIn("编辑画面调色", payload["filterMarkup"])
        self.assertIn('id="editorColorGradeBrightness"', payload["filterMarkup"])
        self.assertIn('value="123"', payload["filterMarkup"])
        self.assertIn('value="-12"', payload["filterMarkup"])
        self.assertIn("编辑景深模糊", payload["blurMarkup"])
        self.assertIn('value="full" selected', payload["blurMarkup"])
        self.assertIn("台词可读性", payload["readableMarkup"])
        self.assertIn("建议拆分", payload["readableMarkup"])
        self.assertIn("拆成长文本卡片", payload["readableMarkup"])
        self.assertIn("编辑这句台词", payload["dialogueMarkup"])
        self.assertIn("这句还没有语音", payload["dialogueMarkup"])
        self.assertIn('data-scene-id="scene_a"', payload["dialogueMarkup"])
        self.assertIn('data-block-id="block_1"', payload["dialogueMarkup"])
        self.assertIn("你好 &lt;世界&gt;", payload["dialogueMarkup"])
        self.assertIn("女主 &amp; A", payload["dialogueMarkup"])
        self.assertIn("这句已经绑好语音", payload["boundDialogueMarkup"])
        self.assertIn("第一句语音", payload["boundDialogueMarkup"])
        self.assertIn("编辑这个选项分支", payload["choiceMarkup"])
        self.assertIn('data-choice-count="1"', payload["choiceMarkup"])
        self.assertIn('data-choice-row="0/1"', payload["choiceMarkup"])
        self.assertIn("选项按钮区", payload["choiceCountMarkup"])
        self.assertIn("is-warning", payload["choiceCountMarkup"])
        self.assertIn("当前有 5 个选项 &lt;偏多&gt;", payload["choiceCountMarkup"])
        self.assertIn("按钮偏多", payload["choiceCountMarkup"])
        self.assertIn("编辑这段旁白", payload["narrationMarkup"])
        self.assertIn("旁白 &lt;内容&gt;", payload["narrationMarkup"])
        self.assertIn("编辑背景切换", payload["backgroundMarkup"])
        self.assertIn("教室 &lt;黄昏&gt;", payload["backgroundMarkup"])
        self.assertIn("天台 3D · 3D 场景", payload["backgroundMarkup"])
        self.assertIn('value="scene_3d" selected', payload["backgroundMarkup"])
        self.assertIn('data-basic="true"', payload["backgroundMarkup"])
        self.assertIn('id="editorScene3dYaw"', payload["backgroundMarkup"])
        self.assertIn('value="45"', payload["backgroundMarkup"])
        self.assertNotIn('id="editorScene3dInteractionEnabled" type="checkbox" checked', payload["backgroundMarkup"])
        self.assertIn("编辑角色出场", payload["characterShowMarkup"])
        self.assertIn('id="editorCharacterId"', payload["characterShowMarkup"])
        self.assertIn('id="editorExpressionId"', payload["characterShowMarkup"])
        self.assertIn('id="editorCharacterPosition"', payload["characterShowMarkup"])
        self.assertIn('data-stage-x="12"', payload["characterShowMarkup"])
        self.assertIn("编辑角色退场", payload["characterHideMarkup"])
        self.assertIn("隐藏哪个角色", payload["characterHideMarkup"])
        self.assertIn('value="fade" selected', payload["characterHideMarkup"])
        self.assertIn("编辑背景音乐", payload["musicMarkup"])
        self.assertIn('value="bgm_1" selected', payload["musicMarkup"])
        self.assertIn("editorMusicEndMode", payload["musicMarkup"])
        self.assertIn("editorMusicEndBlockId", payload["musicMarkup"])
        self.assertIn('value="1200"', payload["musicMarkup"])
        self.assertIn("编辑停止音乐", payload["musicStopMarkup"])
        self.assertIn('value="500"', payload["musicStopMarkup"])
        self.assertIn("编辑音效播放", payload["sfxMarkup"])
        self.assertIn("门铃", payload["sfxMarkup"])
        self.assertIn("编辑视频播放", payload["videoMarkup"])
        self.assertIn("OP &lt;Movie&gt;", payload["videoMarkup"])
        self.assertIn('value="cover" selected', payload["videoMarkup"])
        self.assertIn('value="75" selected', payload["videoMarkup"])
        self.assertIn("必须播放完", payload["videoMarkup"])
        self.assertIn("编辑片尾演职人员表", payload["creditsMarkup"])
        self.assertIn("STAFF &lt;END&gt;", payload["creditsMarkup"])
        self.assertIn("Thanks &amp; Love", payload["creditsMarkup"])
        self.assertIn("企划：A", payload["creditsMarkup"])
        self.assertIn('value="light" selected', payload["creditsMarkup"])
        self.assertIn("编辑场景跳转", payload["jumpMarkup"])
        self.assertIn('value="scene_b" selected', payload["jumpMarkup"])
        self.assertIn("还没有 &lt;变量&gt;", payload["starterMarkup"])
        self.assertIn("先创建 &amp; 再继续", payload["starterMarkup"])
        self.assertIn("编辑变量设置", payload["variableSetMarkup"])
        self.assertIn("文本 &lt;路线&gt;", payload["variableSetMarkup"])
        self.assertIn('value="route:common"', payload["variableSetMarkup"])
        self.assertIn("编辑数字变量变化", payload["variableAddMarkup"])
        self.assertIn('data-filter="number"', payload["variableAddMarkup"])
        self.assertIn('value="3.5"', payload["variableAddMarkup"])
        self.assertIn("判断 2", payload["ruleMarkup"])
        self.assertIn('value="score:5"', payload["ruleMarkup"])
        self.assertIn("条件分支 1", payload["branchMarkup"])
        self.assertIn('data-branch-id="branch&quot;1"', payload["branchMarkup"])
        self.assertIn('data-rendered-rule="0/1"', payload["branchMarkup"])
        self.assertIn('data-action="move-condition-branch-up" disabled', payload["branchMarkup"])
        self.assertIn('value="scene_b" selected', payload["branchMarkup"])
        self.assertIn('data-action="add-condition-rule" data-branch-id="branch&quot;1"', payload["branchMarkup"])
        self.assertIn('data-action="remove-condition-branch" data-branch-id="branch&quot;1"', payload["branchMarkup"])
        self.assertIn("编辑条件判断", payload["conditionMarkup"])
        self.assertIn("<dt>当前分支数</dt><dd>1</dd>", payload["conditionMarkup"])
        self.assertIn("<dt>没命中时去哪里</dt><dd>普通结局</dd>", payload["conditionMarkup"])
        self.assertIn('id="conditionBranchesEditor"', payload["conditionMarkup"])
        self.assertIn('data-condition-branch-row="0/1"', payload["conditionMarkup"])
        self.assertIn('id="editorConditionElseSceneId"', payload["conditionMarkup"])
        self.assertIn('value="scene_c" selected', payload["conditionMarkup"])
        self.assertIn('data-action="add-condition-branch"', payload["conditionMarkup"])
        self.assertIn("附加效果 2", payload["effectMarkup"])
        self.assertIn('data-filter="number"', payload["effectMarkup"])
        self.assertIn('value="variable_add:score:2"', payload["effectMarkup"])
        self.assertIn("data-choice-effects-empty", payload["emptyMarkup"])
        self.assertIn('data-option-id="opt&quot;1"', payload["optionMarkup"])
        self.assertIn("一起 &lt;回家&gt;", payload["optionMarkup"])
        self.assertIn("结尾 &amp; 真相", payload["optionMarkup"])
        self.assertIn('value="scene_b" selected', payload["optionMarkup"])
        self.assertIn('data-rendered-effect="0/1"', payload["optionMarkup"])
        self.assertIn("还有 1 条暂时不支持可视化编辑的旧效果", payload["optionMarkup"])


if __name__ == "__main__":
    unittest.main()
