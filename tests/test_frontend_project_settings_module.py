from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_settings.js"


class FrontendProjectSettingsModuleTests(unittest.TestCase):
    def test_project_settings_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectSettings;
            const options = {{
              saveSlotCountLimits: {{ min: 3, max: 120 }},
              defaultRuntimeSettings: {{
                formalSaveSlotCount: 24,
                defaultTextSpeed: "normal",
                defaultDialogTheme: "project",
                defaultUiThemeMode: "auto",
                defaultBgmVolume: 72,
                defaultSfxVolume: 85,
                defaultVoiceVolume: 92,
                defaultVoiceEnabled: true,
                defaultVoiceDuckingEnabled: true,
              }},
              runtimeTextSpeedLabels: {{ slow: "慢一点", normal: "正常", fast: "快一点", instant: "立刻显示" }},
              runtimeDialogThemeLabels: {{ project: "项目样式", warm: "暖光标准", paper: "纸页回忆" }},
              runtimeUiThemeModeLabels: {{ auto: "自动", light: "浅色", dark: "深色" }},
              dialogBoxPresetLabels: {{ moonlight: "夜色玻璃", warm: "暖光标准", custom: "自定义样式" }},
              dialogBoxShapeLabels: {{ rounded: "圆角框", square: "方角框", capsule: "胶囊框" }},
              dialogBoxAnchorLabels: {{ bottom: "底部", center: "居中", free: "自由" }},
              defaultDialogBoxConfig: {{
                preset: "moonlight",
                shape: "rounded",
                widthPercent: 76,
                minHeight: 148,
                paddingX: 18,
                paddingY: 14,
                backgroundColor: "#0c1422",
                backgroundOpacity: 92,
                borderColor: "#79dcff",
                borderOpacity: 18,
                textColor: "#f3f6ff",
                speakerColor: "#ffffff",
                hintColor: "#c8d6ea",
                blurStrength: 10,
                borderWidth: 1,
                shadowStrength: 30,
                panelAssetOpacity: 0,
                panelAssetFit: "cover",
                anchor: "bottom",
                offsetXPercent: 0,
                offsetYPercent: 0,
              }},
              dialogBoxPresets: {{
                warm: {{
                  preset: "warm",
                  backgroundColor: "#fffaf5",
                  textColor: "#332117",
                }},
              }},
              gameUiPresetLabels: {{ stellar: "神秘科技", minimal: "极简透明", custom: "自定义" }},
              gameUiLayoutLabels: {{ balanced: "标准", minimal: "沉浸", custom: "自定义" }},
              gameUiTitleLayoutLabels: {{ center: "居中", left: "左侧", poster: "海报" }},
              gameUiFontLabels: {{ modern: "现代", serif: "衬线", rounded: "圆润" }},
              gameUiSurfaceLabels: {{ glass: "玻璃", solid: "实色", minimal: "线框" }},
              gameUiBrandLabels: {{ project: "项目", engine: "引擎", hidden: "隐藏" }},
              gameUiSidePanelLabels: {{ full: "完整", compact: "紧凑", hidden: "隐藏" }},
              gameUiSidePositionLabels: {{ right: "右", left: "左" }},
              gameUiTopbarPositionLabels: {{ top: "上", bottom: "下", hidden: "隐藏" }},
              gameUiHudPositionLabels: {{ top: "顶部", "bottom-left": "左下", hidden: "隐藏" }},
              gameUiTitleCardAnchorLabels: {{ center: "中", left: "左", bottom: "下", free: "自由" }},
              defaultGameUiConfig: {{
                preset: "stellar",
                layoutPreset: "balanced",
                titleLayout: "center",
                fontStyle: "modern",
                fontFamily: "",
                fontAssetId: "",
                surfaceStyle: "glass",
                brandMode: "project",
                sidePanelMode: "full",
                sidePanelPosition: "right",
                topbarPosition: "top",
                hudPosition: "top",
                titleCardAnchor: "center",
                titleCardOffsetXPercent: 0,
                titleCardOffsetYPercent: 0,
                layoutGap: 20,
                sidePanelWidth: 320,
                backgroundColor: "#071120",
                backgroundAccentColor: "#6bd5ff",
                panelColor: "#0c1422",
                panelOpacity: 88,
                textColor: "#f3f7ff",
                mutedTextColor: "#bacce4",
                accentColor: "#79dcff",
                accentAltColor: "#7b7cff",
                buttonTextColor: "#f8fcff",
                borderColor: "#79dcff",
                borderOpacity: 18,
                cornerRadius: 22,
                backdropBlur: 14,
                stageVignette: 42,
                motionIntensity: 70,
                titleBackgroundOpacity: 42,
                titleBackgroundFit: "cover",
                panelFrameOpacity: 18,
                panelFrameSlice: {{ top: 24, right: 24, bottom: 24, left: 24 }},
                buttonFrameOpacity: 24,
                buttonFrameSlice: {{ top: 18, right: 18, bottom: 18, left: 18 }},
                uiOverlayOpacity: 8,
              }},
              gameUiPresets: {{
                minimal: {{
                  preset: "minimal",
                  layoutPreset: "minimal",
                  titleLayout: "poster",
                  sidePanelMode: "hidden",
                  topbarPosition: "hidden",
                  hudPosition: "hidden",
                  panelOpacity: 48,
                  motionIntensity: 10,
                }},
              }},
            }};
            const project = {{
              resolution: {{ width: "1920", height: "bad" }},
              runtimeSettings: {{
                formalSaveSlotCount: "999",
                defaultTextSpeed: "instant",
                defaultDialogTheme: "paper",
                defaultUiThemeMode: "dark",
                defaultBgmVolume: "150",
                defaultSfxVolume: "bad",
                defaultVoiceVolume: "-5",
                defaultVoiceEnabled: false,
                defaultVoiceDuckingEnabled: false,
              }},
              dialogBoxConfig: {{
                preset: "warm",
                shape: "capsule",
                widthPercent: 999,
                minHeight: 40,
                paddingX: 100,
                paddingY: 2,
                backgroundColor: "#ABCDEF",
                borderColor: "not-a-color",
                textColor: "#123456",
                backgroundOpacity: -20,
                borderOpacity: 200,
                blurStrength: 99,
                borderWidth: 8,
                shadowStrength: -5,
                panelAssetId: "  ui_panel  ",
                panelAssetOpacity: 144,
                panelAssetFit: "contain",
                anchor: "broken",
                offsetXPercent: 80,
                offsetYPercent: -80,
              }},
              gameUiConfig: {{
                preset: "minimal",
                layoutPreset: "broken",
                titleLayout: "left",
                fontStyle: "serif",
                fontFamily: "  Very Long Font Name ".repeat(8),
                fontAssetId: " font_a ",
                surfaceStyle: "solid",
                brandMode: "engine",
                sidePanelMode: "compact",
                sidePanelPosition: "left",
                topbarPosition: "bottom",
                hudPosition: "bottom-left",
                titleCardAnchor: "free",
                titleCardOffsetXPercent: 99,
                titleCardOffsetYPercent: -99,
                layoutGap: 1,
                sidePanelWidth: 900,
                backgroundColor: "#101010",
                backgroundAccentColor: "bad",
                panelOpacity: 10,
                borderOpacity: 180,
                cornerRadius: 100,
                backdropBlur: -5,
                stageVignette: 120,
                motionIntensity: -20,
                titleBackgroundFit: "contain",
                titleBackgroundOpacity: 101,
                titleLogoAssetId: " logo ",
                panelFrameSlice: {{ top: -5, right: 120, bottom: 32, left: "bad" }},
                buttonFrameSlice: {{ top: 12, right: 14, bottom: 16, left: 18 }},
                uiOverlayOpacity: 101,
              }},
            }};
            const result = {{
              keys: Object.keys(tools).sort(),
              resolution: tools.getProjectResolution(project),
              resolutionLabels: [
                tools.getResolutionLabel(1280, 720),
                tools.getResolutionLabel(1024, 768),
              ],
              screenLabels: [
                tools.getScreenLabel("story"),
                tools.getScreenLabel("custom_screen"),
                tools.getScreenLabel(null),
              ],
              stageStyles: [
                tools.getStageContainerStyle(project),
                tools.getStageContainerStyle(project, {{ large: true }}),
              ],
              resolutionButtons: tools.renderResolutionButtons({{ resolution: {{ width: 1920, height: 1080 }} }}),
              slots: [
                tools.getSafeProjectFormalSaveSlotCount(0, options),
                tools.getSafeProjectFormalSaveSlotCount(2, options),
                tools.getSafeProjectFormalSaveSlotCount(200, options),
                tools.getProjectFormalSaveSlotCount(project, options),
              ],
              safeRuntimeValues: [
                tools.getSafeProjectRuntimeTextSpeed("broken", options),
                tools.getSafeProjectRuntimeDialogTheme("paper", options),
                tools.getSafeProjectRuntimeUiThemeMode("bad", options),
                tools.getSafeProjectRuntimeVolume("bad", 64, options),
                tools.getSafeProjectRuntimeVolume(120, 64, options),
              ],
              runtimeConfig: tools.getProjectRuntimeSettings(project, options),
              safeDialogValues: [
                tools.getSafeProjectDialogBoxPreset("bad", options),
                tools.getSafeProjectDialogBoxShape("square", options),
                tools.getSafeProjectDialogBoxAnchor("free", options),
              ],
              dialogConfig: tools.getProjectDialogBoxConfig(project, options),
              safeGameValues: [
                tools.getSafeProjectGameUiPreset("bad", options),
                tools.getSafeProjectGameUiLayoutPreset("bad", options),
                tools.getSafeProjectGameUiHudPosition("bottom-left", options),
                tools.getSafeProjectGameUiTitleCardAnchor("bad", options),
              ],
              gameConfig: tools.getProjectGameUiConfig(project, options),
              rgba: [
                tools.toRgbaString("#ABCDEF", 25, options),
                tools.toRgbaString("bad", 250, options),
              ],
              radii: [
                tools.getDialogShapeRadius("square", 20, options),
                tools.getDialogShapeRadius("capsule", 20, options),
                tools.getDialogShapeRadius("rounded", 99, options),
              ],
              frameFallback: tools.getSafeGameUiFrameSlice(null, {{ top: 8, right: 10, bottom: 12, left: 14 }}, options),
              exportedDialogLabels: tools.PROJECT_DIALOG_BOX_PRESET_LABELS,
              defaultDialogPreset: tools.getProjectDialogBoxPresetConfig("paper"),
              defaultDialogConfig: tools.getProjectDialogBoxConfig({{
                dialogBoxConfig: {{
                  preset: "transparent",
                  shape: "broken",
                  widthPercent: 10,
                  backgroundColor: "not-a-color",
                  anchor: "free",
                  offsetXPercent: 99,
                }},
              }}),
              exportedGameUiLabels: tools.PROJECT_GAME_UI_PRESET_LABELS,
              defaultGameUiPreset: tools.getProjectGameUiPresetConfig("warm"),
              defaultGameUiConfig: tools.getProjectGameUiConfig({{
                gameUiConfig: {{
                  preset: "paper",
                  layoutPreset: "broken",
                  hudPosition: "bottom-left",
                  sidePanelWidth: 999,
                  panelFrameSlice: {{ top: -9, right: 12, bottom: 14, left: 16 }},
                }},
              }}),
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
        self.assertIn("getProjectGameUiConfig", payload["keys"])
        self.assertEqual(payload["resolution"], {"width": 1920, "height": 720})
        self.assertEqual(payload["resolutionLabels"], ["HD 1280 × 720", "1024 × 768"])
        self.assertEqual(payload["screenLabels"], ["写剧情", "custom_screen", "页面"])
        self.assertEqual(payload["stageStyles"], ["--stage-ratio: 1920 / 720;", "--stage-ratio: 1920 / 720; max-width: 100%;"])
        self.assertIn('data-action="set-resolution"', payload["resolutionButtons"])
        self.assertIn('data-width="1920"', payload["resolutionButtons"])
        self.assertIn("toolbar-button-primary", payload["resolutionButtons"])
        self.assertEqual(payload["slots"], [3, 3, 120, 120])
        self.assertEqual(payload["safeRuntimeValues"], ["normal", "paper", "auto", 64, 100])
        self.assertEqual(
            payload["runtimeConfig"],
            {
                "formalSaveSlotCount": 120,
                "defaultTextSpeed": "instant",
                "defaultDialogTheme": "paper",
                "defaultUiThemeMode": "dark",
                "defaultBgmVolume": 100,
                "defaultSfxVolume": 85,
                "defaultVoiceVolume": 0,
                "defaultVoiceEnabled": False,
                "defaultVoiceDuckingEnabled": False,
            },
        )
        self.assertEqual(payload["safeDialogValues"], ["moonlight", "square", "free"])
        self.assertEqual(payload["dialogConfig"]["preset"], "warm")
        self.assertEqual(payload["dialogConfig"]["shape"], "capsule")
        self.assertEqual(payload["dialogConfig"]["widthPercent"], 100)
        self.assertEqual(payload["dialogConfig"]["minHeight"], 96)
        self.assertEqual(payload["dialogConfig"]["paddingX"], 72)
        self.assertEqual(payload["dialogConfig"]["paddingY"], 6)
        self.assertEqual(payload["dialogConfig"]["backgroundColor"], "#abcdef")
        self.assertEqual(payload["dialogConfig"]["borderColor"], "#79dcff")
        self.assertEqual(payload["dialogConfig"]["backgroundOpacity"], 0)
        self.assertEqual(payload["dialogConfig"]["borderOpacity"], 100)
        self.assertEqual(payload["dialogConfig"]["blurStrength"], 24)
        self.assertEqual(payload["dialogConfig"]["borderWidth"], 4)
        self.assertEqual(payload["dialogConfig"]["shadowStrength"], 0)
        self.assertEqual(payload["dialogConfig"]["panelAssetId"], "ui_panel")
        self.assertEqual(payload["dialogConfig"]["panelAssetOpacity"], 100)
        self.assertEqual(payload["dialogConfig"]["panelAssetFit"], "contain")
        self.assertEqual(payload["dialogConfig"]["anchor"], "bottom")
        self.assertEqual(payload["dialogConfig"]["offsetXPercent"], 35)
        self.assertEqual(payload["dialogConfig"]["offsetYPercent"], -35)
        self.assertEqual(payload["safeGameValues"], ["stellar", "balanced", "bottom-left", "center"])
        self.assertEqual(payload["gameConfig"]["preset"], "minimal")
        self.assertEqual(payload["gameConfig"]["layoutPreset"], "balanced")
        self.assertEqual(payload["gameConfig"]["titleLayout"], "left")
        self.assertEqual(payload["gameConfig"]["sidePanelWidth"], 460)
        self.assertEqual(payload["gameConfig"]["panelOpacity"], 35)
        self.assertEqual(payload["gameConfig"]["borderOpacity"], 100)
        self.assertEqual(payload["gameConfig"]["cornerRadius"], 42)
        self.assertEqual(payload["gameConfig"]["backdropBlur"], 0)
        self.assertEqual(payload["gameConfig"]["stageVignette"], 80)
        self.assertEqual(payload["gameConfig"]["motionIntensity"], 0)
        self.assertEqual(payload["gameConfig"]["titleBackgroundFit"], "contain")
        self.assertEqual(payload["gameConfig"]["titleBackgroundOpacity"], 100)
        self.assertEqual(payload["gameConfig"]["titleLogoAssetId"], "logo")
        self.assertEqual(payload["gameConfig"]["panelFrameSlice"], {"top": 0, "right": 96, "bottom": 32, "left": 24})
        self.assertEqual(payload["gameConfig"]["buttonFrameSlice"], {"top": 12, "right": 14, "bottom": 16, "left": 18})
        self.assertEqual(payload["gameConfig"]["uiOverlayOpacity"], 100)
        self.assertLessEqual(len(payload["gameConfig"]["fontFamily"]), 80)
        self.assertEqual(payload["rgba"], ["rgba(171, 205, 239, 0.25)", "rgba(255, 255, 255, 1.00)"])
        self.assertEqual(payload["radii"], [6, 999, 42])
        self.assertEqual(payload["frameFallback"], {"top": 8, "right": 10, "bottom": 12, "left": 14})
        self.assertEqual(payload["exportedDialogLabels"]["moonlight"], "夜色玻璃")
        self.assertEqual(payload["exportedDialogLabels"]["custom"], "自定义样式")
        self.assertEqual(payload["defaultDialogPreset"]["preset"], "paper")
        self.assertEqual(payload["defaultDialogPreset"]["shape"], "square")
        self.assertEqual(payload["defaultDialogConfig"]["preset"], "transparent")
        self.assertEqual(payload["defaultDialogConfig"]["shape"], "rounded")
        self.assertEqual(payload["defaultDialogConfig"]["widthPercent"], 55)
        self.assertEqual(payload["defaultDialogConfig"]["backgroundColor"], "#08111b")
        self.assertEqual(payload["defaultDialogConfig"]["anchor"], "free")
        self.assertEqual(payload["defaultDialogConfig"]["offsetXPercent"], 35)
        self.assertEqual(payload["exportedGameUiLabels"]["stellar"], "神秘科技")
        self.assertEqual(payload["exportedGameUiLabels"]["custom"], "自定义皮肤")
        self.assertEqual(payload["defaultGameUiPreset"]["preset"], "warm")
        self.assertEqual(payload["defaultGameUiPreset"]["fontStyle"], "rounded")
        self.assertEqual(payload["defaultGameUiConfig"]["preset"], "paper")
        self.assertEqual(payload["defaultGameUiConfig"]["layoutPreset"], "balanced")
        self.assertEqual(payload["defaultGameUiConfig"]["hudPosition"], "bottom-left")
        self.assertEqual(payload["defaultGameUiConfig"]["sidePanelWidth"], 460)
        self.assertEqual(payload["defaultGameUiConfig"]["panelFrameSlice"], {"top": 0, "right": 12, "bottom": 14, "left": 16})


if __name__ == "__main__":
    unittest.main()
