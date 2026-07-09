(function attachEditorModuleGuard(global) {
  const REQUIRED_EDITOR_MODULES = Object.freeze([
    { globalName: "CanvasiaRuntimeConditions", script: "../export_player_template/runtime_conditions.js", label: "运行条件系统" },
    { globalName: "CanvasiaEditorStoryBlockCatalog", script: "./modules/story_block_catalog.js", label: "剧情卡片目录" },
    { globalName: "CanvasiaEditorStoryBlockActions", script: "./modules/story_block_actions.js", label: "剧情卡片动作" },
    { globalName: "CanvasiaEditorStoryBlockEditors", script: "./modules/story_block_editors.js", label: "剧情卡片编辑器" },
    { globalName: "CanvasiaEditorMusicRangeScope", script: "./modules/music_range_scope.js", label: "音乐范围系统" },
    { globalName: "CanvasiaEditorStoryTemplates", script: "./modules/story_templates.js", label: "剧情模板" },
    { globalName: "CanvasiaEditorStoryTemplateApplication", script: "./modules/story_template_application.js", label: "剧情模板应用" },
    { globalName: "CanvasiaEditorStoryTemplatePanel", script: "./modules/story_template_panel.js", label: "剧情模板面板" },
    { globalName: "CanvasiaEditorCommon", script: "./modules/editor_common.js", label: "编辑器通用工具" },
    { globalName: "CanvasiaEditorExportFileNames", script: "./modules/export_file_names.js", label: "导出文件命名" },
    { globalName: "CanvasiaEditorExportReportDescriptions", script: "./modules/export_report_descriptions.js", label: "导出报告说明" },
    { globalName: "CanvasiaEditorVariables", script: "./modules/variables.js", label: "变量系统" },
    { globalName: "CanvasiaEditorProjectRuntimeSettings", script: "./modules/project_runtime_settings.js", label: "运行设置" },
    { globalName: "CanvasiaEditorProjectRuntimeSettingsPanel", script: "./modules/project_runtime_settings_panel.js", label: "运行设置面板" },
    { globalName: "CanvasiaEditorProjectSettings", script: "./modules/project_settings.js", label: "项目设置" },
    { globalName: "CanvasiaEditorDialogBoxReadability", script: "./modules/dialog_box_readability.js", label: "文本框可读性检查" },
    { globalName: "CanvasiaEditorValidationCache", script: "./modules/validation_cache.js", label: "项目巡检缓存" },
    { globalName: "CanvasiaEditorSystemDialog", script: "./modules/system_dialog.js", label: "系统对话框" },
    { globalName: "CanvasiaEditorUiTheme", script: "./modules/ui_theme.js", label: "界面主题" },
    { globalName: "CanvasiaEditorPreviewSave", script: "./modules/preview_save.js", label: "预览存档" },
    { globalName: "CanvasiaEditorRecentWorkspace", script: "./modules/recent_workspace.js", label: "最近工作区" },
    { globalName: "CanvasiaEditorFilters", script: "./modules/editor_filters.js", label: "筛选器" },
    { globalName: "CanvasiaEditorDashboardSearchPanel", script: "./modules/dashboard_search_panel.js", label: "首页搜索面板" },
    { globalName: "CanvasiaEditorDashboardPrimaryActions", script: "./modules/dashboard_primary_actions.js", label: "首页主操作" },
    { globalName: "CanvasiaEditorDashboardProduction", script: "./modules/dashboard_production.js", label: "制作看板" },
    { globalName: "CanvasiaEditorSceneChecklistFocus", script: "./modules/scene_checklist_focus.js", label: "可试玩清单焦点" },
    { globalName: "CanvasiaEditorScriptReadability", script: "./modules/script_readability.js", label: "台词可读性" },
    { globalName: "CanvasiaEditorScenePacingAdvisor", script: "./modules/scene_pacing_advisor.js", label: "场景节奏建议" },
    { globalName: "CanvasiaEditorScenePolish", script: "./modules/scene_polish.js", label: "场景润色" },
    { globalName: "CanvasiaEditorSceneMoodRecipes", script: "./modules/scene_mood_recipes.js", label: "场景氛围配方" },
    { globalName: "CanvasiaEditorStorySceneStructurePanel", script: "./modules/story_scene_structure_panel.js", label: "剧情结构面板" },
    { globalName: "CanvasiaEditorScriptVoice", script: "./modules/script_voice.js", label: "台词语音" },
    { globalName: "CanvasiaEditorVoiceMatchReviewPanel", script: "./modules/voice_match_review_panel.js", label: "语音匹配复核" },
    { globalName: "CanvasiaEditorVoiceProductionSheet", script: "./modules/voice_production_sheet.js", label: "语音制作表" },
    { globalName: "CanvasiaEditorScreenplayExporter", script: "./modules/screenplay_exporter.js", label: "剧本导出" },
    { globalName: "CanvasiaEditorRenpyExporter", script: "./modules/renpy_exporter.js", label: "Ren'Py 导出" },
    { globalName: "CanvasiaEditorAudioTimingEstimator", script: "./modules/audio_timing_estimator.js", label: "音频时长估算" },
    { globalName: "CanvasiaEditorDirectorCueSheet", script: "./modules/director_cue_sheet.js", label: "导演提示表" },
    { globalName: "CanvasiaEditorScriptImporter", script: "./modules/script_importer.js", label: "剧本导入" },
    { globalName: "CanvasiaEditorScriptImporterPanel", script: "./modules/script_importer_panel.js", label: "剧本导入面板" },
    { globalName: "CanvasiaEditorScriptImportMapping", script: "./modules/script_import_mapping.js", label: "剧本导入映射" },
    { globalName: "CanvasiaEditorRouteAnalyzer", script: "./modules/route_analyzer.js", label: "路线分析" },
    { globalName: "CanvasiaEditorRouteTestingReport", script: "./modules/route_testing_report.js", label: "路线测试报告" },
    { globalName: "CanvasiaEditorSceneProductionBoard", script: "./modules/scene_production_board.js", label: "场景制作看板" },
    { globalName: "CanvasiaEditorPreviewRegression", script: "./modules/preview_regression.js", label: "预览回归测试" },
    { globalName: "CanvasiaEditorRegressionDiagnostics", script: "./modules/regression_diagnostics.js", label: "回归诊断" },
    { globalName: "CanvasiaEditorPlaytestHandoffReport", script: "./modules/playtest_handoff_report.js", label: "试玩交接报告" },
    { globalName: "CanvasiaEditorChoiceConsequenceSheet", script: "./modules/choice_consequence_sheet.js", label: "选项后果表" },
    { globalName: "CanvasiaEditorVariableInfluenceSheet", script: "./modules/variable_influence_sheet.js", label: "变量影响表" },
    { globalName: "CanvasiaEditorAudioCueSheet", script: "./modules/audio_cue_sheet.js", label: "音频调度表" },
    { globalName: "CanvasiaEditorRuntimeCapabilityMatrix", script: "./modules/runtime_capability_matrix.js", label: "运行能力矩阵" },
    { globalName: "CanvasiaEditorProjectPolish", script: "./modules/project_polish.js", label: "项目一键打磨" },
    { globalName: "CanvasiaEditorProjectPolishReceiptPanel", script: "./modules/project_polish_receipt_panel.js", label: "打磨回执面板" },
    { globalName: "CanvasiaEditorAudioCueSheetPanel", script: "./modules/audio_cue_sheet_panel.js", label: "音频调度面板" },
    { globalName: "CanvasiaEditorStageDirectionSheet", script: "./modules/stage_direction_sheet.js", label: "舞台调度表" },
    { globalName: "CanvasiaEditorStageDirectionSheetPanel", script: "./modules/stage_direction_sheet_panel.js", label: "舞台调度面板" },
    { globalName: "CanvasiaEditorPresentationTimeline", script: "./modules/presentation_timeline.js", label: "演出时间轴" },
    { globalName: "CanvasiaEditorPresentationTimelinePanel", script: "./modules/presentation_timeline_panel.js", label: "演出时间轴面板" },
    { globalName: "CanvasiaEditorLocalizationCoverage", script: "./modules/localization_coverage.js", label: "多语言覆盖" },
    { globalName: "CanvasiaEditorLocalizationCoveragePanel", script: "./modules/localization_coverage_panel.js", label: "多语言覆盖面板" },
    { globalName: "CanvasiaEditorProductionBacklog", script: "./modules/production_backlog.js", label: "制作待办" },
    { globalName: "CanvasiaEditorReleaseCandidateManifest", script: "./modules/release_candidate_manifest.js", label: "候选发布清单" },
    { globalName: "CanvasiaEditorReleaseEvidencePack", script: "./modules/release_evidence_pack.js", label: "发布证据包" },
    { globalName: "CanvasiaEditorUnlockableContentManifest", script: "./modules/unlockable_content_manifest.js", label: "解锁内容清单" },
    { globalName: "CanvasiaEditorVisualEffects", script: "./modules/visual_effects.js", label: "视觉演出" },
    { globalName: "CanvasiaEditorParticleEffects", script: "./modules/particle_effects.js", label: "粒子系统" },
    { globalName: "CanvasiaEditorProjectHistory", script: "./modules/project_history.js", label: "项目历史" },
    { globalName: "CanvasiaEditorProjectHistoryPanel", script: "./modules/project_history_panel.js", label: "项目历史面板" },
    { globalName: "CanvasiaEditorAssetUsageMap", script: "./modules/asset_usage_map.js", label: "素材引用图" },
    { globalName: "CanvasiaEditorAssetCatalog", script: "./modules/asset_catalog.js", label: "素材目录" },
    { globalName: "CanvasiaEditorAssetImportRules", script: "./modules/asset_import_rules.js", label: "素材导入规则" },
    { globalName: "CanvasiaEditorBeginnerAssetsGuide", script: "./modules/beginner_assets_guide.js", label: "新手素材指南" },
    { globalName: "CanvasiaEditorBeginnerCharacterGuide", script: "./modules/beginner_character_guide.js", label: "新手角色指南" },
    { globalName: "CanvasiaEditorCharacterPresentationPanel", script: "./modules/character_presentation_panel.js", label: "角色演出面板" },
    { globalName: "CanvasiaEditorAssetFootprint", script: "./modules/asset_footprint.js", label: "素材体积分析" },
    { globalName: "CanvasiaEditorRuntimePreloadBudget", script: "./modules/runtime_preload_budget.js", label: "运行预加载预算" },
    { globalName: "CanvasiaEditorAssetDependencySheet", script: "./modules/asset_dependency_sheet.js", label: "素材依赖表" },
    { globalName: "CanvasiaEditorAssetRightsSheet", script: "./modules/asset_rights_sheet.js", label: "素材授权表" },
    { globalName: "CanvasiaEditorOpenAiAssetGenerator", script: "./modules/openai_asset_generator.js", label: "AI 素材生成" },
    { globalName: "CanvasiaEditorApiEndpoints", script: "./modules/api_endpoints.js", label: "API 端点" },
    { globalName: "CanvasiaEditorBeginnerTutorial", script: "./modules/beginner_tutorial.js", label: "新手教程" },
    { globalName: "CanvasiaEditorProjectCenter", script: "./modules/project_center.js", label: "项目中心" },
    { globalName: "CanvasiaEditorCreativeAssistant", script: "./modules/creative_assistant.js", label: "创作助手" },
    { globalName: "CanvasiaEditorMode", script: "./modules/editor_mode.js", label: "编辑器模式" },
    { globalName: "CanvasiaEditorReleaseVersion", script: "./modules/release_version.js", label: "发布版本" },
    { globalName: "CanvasiaEditorProjectDoctor", script: "./modules/project_doctor.js", label: "项目医生" },
    { globalName: "CanvasiaEditorProjectDoctorPanel", script: "./modules/project_doctor_panel.js", label: "项目医生面板" },
    { globalName: "CanvasiaEditorProjectMilestones", script: "./modules/project_milestones.js", label: "项目里程碑" },
    { globalName: "CanvasiaEditorProjectMilestonePanel", script: "./modules/project_milestones_panel.js", label: "项目里程碑面板" },
    { globalName: "CanvasiaEditorReleaseControl", script: "./modules/release_control.js", label: "发布控制" },
    { globalName: "CanvasiaEditorReleaseControlPanel", script: "./modules/release_control_panel.js", label: "发布控制面板" },
    { globalName: "CanvasiaEditorTypewriter", script: "./modules/typewriter.js", label: "打字机效果" },
    { globalName: "CanvasiaEditorCommandPalette", script: "./modules/command_palette.js", label: "指挥面板" },
  ].map((entry) => Object.freeze(entry)));

  function getRequiredEditorModules() {
    return REQUIRED_EDITOR_MODULES.map((entry) => Object.freeze({ ...entry }));
  }

  function getMissingEditorModules(scope = global) {
    return REQUIRED_EDITOR_MODULES.filter((entry) => !scope[entry.globalName]);
  }

  function buildMissingEditorModulesMessage(missingModules = []) {
    const missing = Array.isArray(missingModules) ? missingModules : [];
    if (!missing.length) {
      return "";
    }

    const preview = missing
      .slice(0, 8)
      .map((entry) => `- ${entry.label} (${entry.script})`)
      .join("\n");
    const hiddenCount = Math.max(missing.length - 8, 0);
    const hiddenLine = hiddenCount > 0 ? `\n- 另有 ${hiddenCount} 个模块也没有载入。` : "";
    return [
      "编辑器启动时发现有核心模块没有载入成功。",
      "",
      preview + hiddenLine,
      "",
      "请先刷新页面；如果仍然出现，请重新运行启动脚本，并确认浏览器没有拦截本地脚本文件。",
    ].join("\n");
  }

  function showModuleLoadError(missingModules = [], options = {}) {
    const doc = options.document ?? global.document;
    const message = buildMissingEditorModulesMessage(missingModules);
    if (!doc || !message) {
      return false;
    }

    doc.getElementById("loadingState")?.classList?.add("is-hidden");
    const errorState = doc.getElementById("errorState");
    const errorMessage = doc.getElementById("errorMessage");
    if (errorMessage) {
      errorMessage.textContent = message;
    }
    errorState?.classList?.remove("is-hidden");
    const reloadButton = errorState?.querySelector?.('[data-action="reload-editor-page"]');
    if (typeof reloadButton?.focus === "function" && options.focus !== false) {
      reloadButton.focus();
    }
    return true;
  }

  function createModuleLoadError(missingModules = []) {
    const error = new Error(buildMissingEditorModulesMessage(missingModules));
    error.name = "CanvasiaEditorModuleLoadError";
    error.isEditorModuleLoadError = true;
    error.missingModules = missingModules.map((entry) => ({ ...entry }));
    return error;
  }

  function assertRequiredModulesReady(options = {}) {
    const scope = options.scope ?? global;
    const missingModules = getMissingEditorModules(scope);
    if (!missingModules.length) {
      return true;
    }

    showModuleLoadError(missingModules, options);
    throw createModuleLoadError(missingModules);
  }

  global.CanvasiaEditorModuleGuard = Object.freeze({
    REQUIRED_EDITOR_MODULES,
    getRequiredEditorModules,
    getMissingEditorModules,
    buildMissingEditorModulesMessage,
    showModuleLoadError,
    createModuleLoadError,
    assertRequiredModulesReady,
  });
})(typeof window !== "undefined" ? window : globalThis);
