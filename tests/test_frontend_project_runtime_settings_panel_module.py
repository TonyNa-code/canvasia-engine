from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_runtime_settings_panel.js"


class FrontendProjectRuntimeSettingsPanelModuleTests(unittest.TestCase):
    def test_panel_renders_runtime_ui_controls_and_asset_options(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectRuntimeSettingsPanel;
            const labels = {{
              languageLabels: {{ "zh-CN": "简体中文", "en-US": "English" }},
              textSpeedLabels: {{ normal: "普通", fast: "快速" }},
              dialogThemeLabels: {{ project: "项目样式", paper: "纸张" }},
              uiThemeModeLabels: {{ auto: "自动", dark: "深色" }},
              performanceProfileLabels: {{ standard: "标准 PC / 网页", web: "网页轻量" }},
              dialogBoxPresetLabels: {{ glass: "玻璃", custom: "自定义" }},
              dialogBoxShapeLabels: {{ rounded: "圆角" }},
              dialogBoxAnchorLabels: {{ bottom: "底部" }},
              gameUiPresetLabels: {{ aurora: "极光", custom: "自定义" }},
              gameUiLayoutLabels: {{ classic: "经典" }},
              gameUiTitleLayoutLabels: {{ centered: "居中" }},
              gameUiFontLabels: {{ modern: "现代" }},
              gameUiSurfaceLabels: {{ glass: "玻璃" }},
              gameUiBrandLabels: {{ subtle: "轻量" }},
              gameUiSidePanelLabels: {{ auto: "自动" }},
              gameUiSidePositionLabels: {{ left: "左侧" }},
              gameUiTopbarPositionLabels: {{ top: "顶部" }},
              gameUiHudPositionLabels: {{ bottom: "底部" }},
              gameUiTitleCardAnchorLabels: {{ center: "中央" }},
            }};
            const baseSlice = {{ top: 12, right: 12, bottom: 12, left: 12 }};
            const model = {{
              labels,
              runtimeSettings: {{
                formalSaveSlotCount: 36,
                defaultTextSpeed: "fast",
                defaultDialogTheme: "project",
                defaultUiThemeMode: "dark",
                performanceProfile: "web",
                defaultBgmVolume: 64,
                defaultSfxVolume: 70,
                defaultVoiceVolume: 80,
                defaultVoiceDuckingRatio: 42,
                defaultVoiceEnabled: true,
                defaultVoiceDuckingEnabled: false,
              }},
              saveSlotLimits: {{ min: 3, max: 120 }},
              dialogBoxConfig: {{
                preset: "glass",
                shape: "rounded",
                anchor: "bottom",
                widthPercent: 88,
                minHeight: 160,
                offsetXPercent: 0,
                offsetYPercent: 4,
                backgroundColor: "#112233",
                backgroundOpacity: 72,
                borderColor: "#335577",
                borderOpacity: 65,
                textColor: "#f8fbff",
                speakerColor: "#9ad4ff",
                blurStrength: 12,
                panelAssetId: "ui_box",
                panelAssetOpacity: 83,
                panelAssetFit: "contain",
              }},
              gameUiConfig: {{
                preset: "aurora",
                layoutPreset: "classic",
                titleLayout: "centered",
                fontStyle: "modern",
                fontFamily: "Noto Serif CJK SC",
                fontAssetId: "",
                surfaceStyle: "glass",
                brandMode: "subtle",
                sidePanelMode: "auto",
                sidePanelPosition: "left",
                topbarPosition: "top",
                hudPosition: "bottom",
                titleCardAnchor: "center",
                titleCardOffsetXPercent: 0,
                titleCardOffsetYPercent: 0,
                layoutGap: 20,
                sidePanelWidth: 320,
                titleBackgroundAssetId: "",
                titleBackgroundFit: "cover",
                titleBackgroundOpacity: 55,
                titleLogoAssetId: "",
                panelFrameAssetId: "ui_box",
                panelFrameOpacity: 80,
                panelFrameSlice: baseSlice,
                buttonFrameAssetId: "ui_button",
                buttonHoverFrameAssetId: "",
                buttonPressedFrameAssetId: "",
                buttonDisabledFrameAssetId: "",
                buttonFrameOpacity: 85,
                buttonFrameSlice: baseSlice,
                saveSlotFrameAssetId: "",
                systemPanelFrameAssetId: "",
                uiOverlayAssetId: "",
                uiOverlayOpacity: 20,
                backgroundColor: "#07111f",
                backgroundAccentColor: "#5aa9ff",
                panelColor: "#101928",
                panelOpacity: 82,
                textColor: "#f7fbff",
                mutedTextColor: "#9aa8bc",
                accentColor: "#64a9ff",
                accentAltColor: "#a489ff",
                buttonTextColor: "#ffffff",
                borderColor: "#28435f",
                borderOpacity: 45,
                cornerRadius: 18,
                backdropBlur: 10,
                stageVignette: 25,
                motionIntensity: 30,
              }},
              projectLanguage: "zh-CN",
              projectSupportedLanguages: ["zh-CN", "en-US"],
              assetContext: {{
                assetList: [
                  {{ id: "ui_box", type: "ui", name: "文本框", path: "ui/box.png", fileExists: true }},
                  {{ id: "ui_button", type: "ui", name: "按钮框", path: "ui/button.png", fileExists: true }},
                  {{ id: "bg_school", type: "background", name: "教室", path: "bg/school.png", fileExists: false }},
                ],
                assetsById: new Map(),
                getAssetTypeLabel(type) {{ return {{ ui: "界面素材", background: "背景" }}[type] || type; }},
              }},
              variableLibraryPanelHtml: "<section>变量库</section>",
              dialogBoxReadabilityReport: {{
                metrics: {{ textBlockCount: 4, longTextCount: 1, multilineCount: 2, textContrastRatio: "4.8" }},
                issues: [{{ title: "对比度偏低", detail: "正文可读性需要增强" }}],
              }},
              dialogBoxReadabilityPlan: {{ changed: true, operations: [{{ label: "提高不透明度" }}] }},
              dialogBoxReadabilityDigest: {{
                level: "warn",
                helperText: "建议自动增强",
                badgeLabel: "需处理",
                actionLabel: "一键增强",
              }},
            }};
            const html = tools.renderProjectRuntimeSettingsPanel(model, {{ escapeHtml: (value) => String(value), dialogBoxReadabilityFixInFlight: false }});
            process.stdout.write(JSON.stringify({{
              hasPerformanceSelect: html.includes('id="projectRuntimePerformanceProfileSelect"'),
              hasPerformanceLabel: html.includes("性能目标"),
              hasDialogAction: html.includes('data-action="apply-dialog-box-readability-fix"'),
              hasGameUiSave: html.includes('data-action="save-project-game-ui-config"'),
              hasAssetName: html.includes("文本框 · box.png"),
              hasVariableHost: html.includes("projectVariableLibraryPanelHost"),
              hasFrameSlice: html.includes("projectGameUiPanelFrameSliceTopInput"),
              hasExportAction: html.includes('data-export-target="web"'),
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
        self.assertTrue(payload["hasPerformanceSelect"])
        self.assertTrue(payload["hasPerformanceLabel"])
        self.assertTrue(payload["hasDialogAction"])
        self.assertTrue(payload["hasGameUiSave"])
        self.assertTrue(payload["hasAssetName"])
        self.assertTrue(payload["hasVariableHost"])
        self.assertTrue(payload["hasFrameSlice"])
        self.assertTrue(payload["hasExportAction"])

    def test_input_readers_delegate_dom_fields_to_normalizers(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectRuntimeSettingsPanel;
            const values = {{
              projectRuntimePerformanceProfileSelect: {{ value: "web" }},
              projectRuntimeDefaultTextSpeedSelect: {{ value: "fast" }},
              projectRuntimeDefaultDialogThemeSelect: {{ value: "project" }},
              projectRuntimeDefaultUiThemeModeSelect: {{ value: "dark" }},
              projectRuntimeDefaultBgmVolumeInput: {{ value: "64" }},
              projectRuntimeDefaultSfxVolumeInput: {{ value: "70" }},
              projectRuntimeDefaultVoiceVolumeInput: {{ value: "80" }},
              projectRuntimeDefaultVoiceDuckingRatioInput: {{ value: "42" }},
              projectRuntimeDefaultVoiceEnabledInput: {{ checked: false }},
              projectRuntimeDefaultVoiceDuckingEnabledInput: {{ checked: true }},
              projectDialogBoxPresetSelect: {{ value: "glass" }},
              projectDialogBoxWidthInput: {{ value: "88" }},
              projectGameUiPresetSelect: {{ value: "aurora" }},
              projectGameUiPanelFrameSliceTopInput: {{ value: "11" }},
              projectGameUiPanelFrameSliceRightInput: {{ value: "12" }},
              projectGameUiPanelFrameSliceBottomInput: {{ value: "13" }},
              projectGameUiPanelFrameSliceLeftInput: {{ value: "14" }},
            }};
            const doc = {{ getElementById(id) {{ return values[id] || {{ value: undefined, checked: true }}; }} }};
            const runtime = tools.readProjectRuntimePlaybackDefaultsFromDocument(
              {{ defaultTextSpeed: "normal", performanceProfile: "standard" }},
              doc,
              (project) => project.runtimeSettings
            );
            const dialog = tools.readProjectDialogBoxConfigFromDocument({{ preset: "custom" }}, doc, (project) => project.dialogBoxConfig);
            const gameUi = tools.readProjectGameUiConfigFromDocument(
              {{ preset: "custom", panelFrameSlice: {{ top: 1, right: 1, bottom: 1, left: 1 }}, buttonFrameSlice: {{ top: 2, right: 2, bottom: 2, left: 2 }} }},
              doc,
              (project) => project.gameUiConfig,
              (slice) => slice
            );
            process.stdout.write(JSON.stringify({{ runtime, dialog, gameUi }}));
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
        self.assertEqual(payload["runtime"]["performanceProfile"], "web")
        self.assertEqual(payload["runtime"]["defaultTextSpeed"], "fast")
        self.assertFalse(payload["runtime"]["defaultVoiceEnabled"])
        self.assertTrue(payload["runtime"]["defaultVoiceDuckingEnabled"])
        self.assertEqual(payload["dialog"]["preset"], "glass")
        self.assertEqual(payload["dialog"]["widthPercent"], "88")
        self.assertEqual(payload["gameUi"]["preset"], "aurora")
        self.assertEqual(payload["gameUi"]["panelFrameSlice"], {"top": "11", "right": "12", "bottom": "13", "left": "14"})


if __name__ == "__main__":
    unittest.main()
