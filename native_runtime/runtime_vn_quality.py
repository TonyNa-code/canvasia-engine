from __future__ import annotations

from pathlib import Path


def build_native_runtime_vn_baseline_quality_report(bundle_dir: Path, deps: dict[str, object]) -> dict:
    DEFAULT_FORMAL_SAVE_SLOT_COUNT = deps['DEFAULT_FORMAL_SAVE_SLOT_COUNT']
    DEFAULT_GAME_DATA_NAME = deps['DEFAULT_GAME_DATA_NAME']
    DEFAULT_PROJECT_LANGUAGE = deps['DEFAULT_PROJECT_LANGUAGE']
    MAX_FORMAL_SAVE_SLOT_COUNT = deps['MAX_FORMAL_SAVE_SLOT_COUNT']
    MIN_FORMAL_SAVE_SLOT_COUNT = deps['MIN_FORMAL_SAVE_SLOT_COUNT']
    SAVE_DIALOG_PAGE_SIZE = deps['SAVE_DIALOG_PAGE_SIZE']
    VN_BASELINE_EFFECT_BLOCK_TYPES = deps['VN_BASELINE_EFFECT_BLOCK_TYPES']
    VN_TEXT_LONG_WARNING_LENGTH = deps['VN_TEXT_LONG_WARNING_LENGTH']
    VN_TEXT_LONG_WARNING_LINES = deps['VN_TEXT_LONG_WARNING_LINES']
    add_vn_baseline_issue = deps['add_vn_baseline_issue']
    build_ending_scene_ids = deps['build_ending_scene_ids']
    collect_scene_outgoing_targets = deps['collect_scene_outgoing_targets']
    condition_operator_matches_variable_type = deps['condition_operator_matches_variable_type']
    count_i18n_translations = deps['count_i18n_translations']
    get_asset_runtime_path = deps['get_asset_runtime_path']
    get_export_variable_map = deps['get_export_variable_map']
    get_project_dialog_box_config = deps['get_project_dialog_box_config']
    get_project_formal_save_slot_count = deps['get_project_formal_save_slot_count']
    get_project_game_ui_config = deps['get_project_game_ui_config']
    get_safe_audio_fade_ms = deps['get_safe_audio_fade_ms']
    get_safe_basic_transition = deps['get_safe_basic_transition']
    get_safe_character_stage = deps['get_safe_character_stage']
    get_safe_character_transition = deps['get_safe_character_transition']
    get_safe_music_end_mode = deps['get_safe_music_end_mode']
    get_safe_transition_duration_ms = deps['get_safe_transition_duration_ms']
    get_vn_baseline_block_text = deps['get_vn_baseline_block_text']
    get_vn_baseline_character_sprite_asset_id = deps['get_vn_baseline_character_sprite_asset_id']
    get_vn_baseline_color_contrast_ratio = deps['get_vn_baseline_color_contrast_ratio']
    get_vn_baseline_font_asset_status = deps['get_vn_baseline_font_asset_status']
    is_vn_baseline_placeholder_asset = deps['is_vn_baseline_placeholder_asset']
    iter_export_scenes = deps['iter_export_scenes']
    load_game_data = deps['load_game_data']
    math = deps['math']
    normalize_language_code = deps['normalize_language_code']
    normalize_supported_languages = deps['normalize_supported_languages']
    normalize_variable_type = deps['normalize_variable_type']
    now_iso = deps['now_iso']

    payload = load_game_data(bundle_dir / DEFAULT_GAME_DATA_NAME)
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    dialog_box_config = get_project_dialog_box_config(project)
    i18n_doc = payload.get("i18n") if isinstance(payload.get("i18n"), dict) else {}
    default_language = normalize_language_code(i18n_doc.get("defaultLanguage") or project.get("language"), DEFAULT_PROJECT_LANGUAGE)
    fallback_language = normalize_language_code(i18n_doc.get("fallbackLanguage"), default_language)
    supported_languages = normalize_supported_languages(
        i18n_doc.get("supportedLanguages") or project.get("supportedLanguages"),
        default_language,
    )
    target_i18n_languages = [language for language in supported_languages if language != default_language]
    runtime_settings = project.get("runtimeSettings") if isinstance(project.get("runtimeSettings"), dict) else {}
    formal_save_slot_count = get_project_formal_save_slot_count(project)
    raw_formal_save_slot_count = runtime_settings.get("formalSaveSlotCount", DEFAULT_FORMAL_SAVE_SLOT_COUNT)
    try:
        configured_formal_save_slot_count = int(raw_formal_save_slot_count)
    except Exception:
        configured_formal_save_slot_count = DEFAULT_FORMAL_SAVE_SLOT_COUNT
    save_dialog_page_count = max(1, math.ceil(formal_save_slot_count / SAVE_DIALOG_PAGE_SIZE))
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    asset_id_counts: dict[str, int] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_id = str(asset.get("id") or "").strip()
        if asset_id:
            asset_id_counts[asset_id] = asset_id_counts.get(asset_id, 0) + 1
    duplicate_asset_ids = sorted(asset_id for asset_id, count in asset_id_counts.items() if count > 1)
    assets_by_id = {str(asset.get("id")): asset for asset in assets if isinstance(asset, dict) and asset.get("id")}
    game_ui_config = get_project_game_ui_config(project)
    font_asset_count = sum(1 for asset in assets if isinstance(asset, dict) and asset.get("type") == "font")
    font_status = get_vn_baseline_font_asset_status(bundle_dir, game_ui_config, assets_by_id)
    video_asset_count = sum(1 for asset in assets if isinstance(asset, dict) and asset.get("type") == "video")
    cg_asset_ids = {
        str(asset.get("id"))
        for asset in assets
        if isinstance(asset, dict) and asset.get("type") == "cg" and str(asset.get("id") or "").strip()
    }
    bgm_asset_ids = {
        str(asset.get("id"))
        for asset in assets
        if isinstance(asset, dict) and asset.get("type") in {"bgm", "audio"} and str(asset.get("id") or "").strip()
    }
    sfx_asset_ids = {
        str(asset.get("id"))
        for asset in assets
        if isinstance(asset, dict) and asset.get("type") == "sfx" and str(asset.get("id") or "").strip()
    }
    voice_asset_ids = {
        str(asset.get("id"))
        for asset in assets
        if isinstance(asset, dict) and asset.get("type") == "voice" and str(asset.get("id") or "").strip()
    }
    i18n_translatable_entry_count = 0
    i18n_expected_translation_count = 0
    i18n_present_translation_count = 0
    variables, variables_by_id, duplicate_variable_ids = get_export_variable_map(payload)
    characters_doc = payload.get("characters") if isinstance(payload.get("characters"), dict) else {}
    characters = characters_doc.get("characters") if isinstance(characters_doc.get("characters"), list) else []
    character_id_counts: dict[str, int] = {}
    duplicate_expression_id_count = 0
    duplicate_expression_id_names: list[str] = []
    for character in characters:
        if not isinstance(character, dict):
            continue
        character_id = str(character.get("id") or "").strip()
        if character_id:
            character_id_counts[character_id] = character_id_counts.get(character_id, 0) + 1
        expressions = character.get("expressions") if isinstance(character.get("expressions"), list) else []
        expression_id_counts: dict[str, int] = {}
        for expression in expressions:
            if not isinstance(expression, dict):
                continue
            expression_id = str(expression.get("id") or "").strip()
            if expression_id:
                expression_id_counts[expression_id] = expression_id_counts.get(expression_id, 0) + 1
        duplicate_expression_ids = sorted(expression_id for expression_id, count in expression_id_counts.items() if count > 1)
        duplicate_expression_id_count += len(duplicate_expression_ids)
        if duplicate_expression_ids:
            character_label = str(character.get("displayName") or character.get("name") or character_id or "未命名角色")
            duplicate_expression_id_names.extend(f"{character_label}:{expression_id}" for expression_id in duplicate_expression_ids)
    duplicate_character_ids = sorted(character_id for character_id, count in character_id_counts.items() if count > 1)
    characters_by_id = {
        str(character.get("id")): character
        for character in characters
        if isinstance(character, dict) and str(character.get("id") or "").strip()
    }
    character_expression_ids_by_id: dict[str, set[str]] = {}
    for character_id, character in characters_by_id.items():
        expected, present = count_i18n_translations(character, "displayName", target_i18n_languages)
        if expected == 0:
            expected, present = count_i18n_translations(character, "name", target_i18n_languages)
        if expected:
            i18n_translatable_entry_count += 1
            i18n_expected_translation_count += expected
            i18n_present_translation_count += present
        expressions = character.get("expressions") if isinstance(character.get("expressions"), list) else []
        character_expression_ids_by_id[character_id] = {
            str(expression.get("id")).strip()
            for expression in expressions
            if isinstance(expression, dict) and str(expression.get("id") or "").strip()
        }
    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
    chapter_id_counts: dict[str, int] = {}
    empty_chapter_count = 0
    empty_chapter_names: list[str] = []
    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        chapter_id = str(chapter.get("id") or chapter.get("chapterId") or "").strip()
        if chapter_id:
            chapter_id_counts[chapter_id] = chapter_id_counts.get(chapter_id, 0) + 1
        chapter_scenes = chapter.get("scenes") if isinstance(chapter.get("scenes"), list) else []
        if not chapter_scenes:
            empty_chapter_count += 1
            empty_chapter_names.append(str(chapter.get("name") or chapter_id or "未命名章节"))
    duplicate_chapter_ids = sorted(chapter_id for chapter_id, count in chapter_id_counts.items() if count > 1)
    scenes = iter_export_scenes(chapters)
    missing_scene_id_count = 0
    missing_scene_id_names: list[str] = []
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("id") or "").strip()
        if not scene_id:
            missing_scene_id_count += 1
            missing_scene_id_names.append(str(scene.get("name") or "未命名场景"))
    scene_ids = [str(scene.get("id") or "").strip() for scene in scenes if isinstance(scene, dict)]
    scene_id_counts: dict[str, int] = {}
    for scene_id in scene_ids:
        if scene_id:
            scene_id_counts[scene_id] = scene_id_counts.get(scene_id, 0) + 1
    duplicate_scene_ids = sorted(scene_id for scene_id, count in scene_id_counts.items() if count > 1)
    valid_scene_ids = {scene_id for scene_id in scene_ids if scene_id}
    entry_scene_id = str(project.get("entrySceneId") or "").strip()

    dialogue_count = 0
    narration_count = 0
    choice_count = 0
    empty_text_count = 0
    condition_count = 0
    condition_branch_count = 0
    condition_rule_count = 0
    condition_empty_branch_count = 0
    missing_navigation_target_count = 0
    missing_navigation_target_names: list[str] = []
    implicit_condition_fallback_end_count = 0
    implicit_condition_fallback_names: list[str] = []
    choice_effect_count = 0
    variable_set_count = 0
    variable_add_count = 0
    variable_written_ids: set[str] = set()
    condition_read_variable_ids: set[str] = set()
    logic_missing_variable_count = 0
    logic_non_number_add_count = 0
    logic_operator_mismatch_count = 0
    character_show_count = 0
    character_move_count = 0
    character_hide_count = 0
    character_transition_count = 0
    character_position_values: set[str] = set()
    character_stage_adjustment_count = 0
    missing_character_ref_count = 0
    missing_character_ref_names: list[str] = []
    missing_expression_ref_count = 0
    missing_expression_ref_names: list[str] = []
    scenes_with_background = 0
    background_block_count = 0
    background_transition_count = 0
    background_asset_ids: set[str] = set()
    cg_used_asset_ids: set[str] = set()
    missing_background_asset_count = 0
    missing_background_asset_names: list[str] = []
    scenes_with_music = 0
    scenes_with_effects = 0
    choice_option_count = 0
    empty_choice_option_count = 0
    long_choice_option_count = 0
    duplicate_choice_option_count = 0
    crowded_choice_block_count = 0
    no_action_choice_option_count = 0
    no_action_choice_option_names: list[str] = []
    same_target_choice_count = 0
    same_target_choice_names: list[str] = []
    same_target_condition_count = 0
    same_target_condition_names: list[str] = []
    sfx_play_count = 0
    missing_sfx_asset_count = 0
    missing_sfx_asset_names: list[str] = []
    video_play_count = 0
    missing_video_asset_count = 0
    missing_video_asset_names: list[str] = []
    credits_roll_count = 0
    credits_line_count = 0
    empty_credits_roll_count = 0
    short_credits_roll_count = 0
    short_credits_roll_names: list[str] = []
    music_play_count = 0
    music_stop_count = 0
    music_scoped_count = 0
    music_fade_in_count = 0
    music_fade_out_count = 0
    music_after_block_scope_count = 0
    missing_music_end_block_count = 0
    missing_music_end_block_names: list[str] = []
    backward_music_end_block_count = 0
    backward_music_end_block_names: list[str] = []
    music_used_asset_ids: set[str] = set()
    missing_music_asset_count = 0
    missing_music_asset_names: list[str] = []
    dialogue_voice_count = 0
    narration_voice_count = 0
    voice_used_asset_ids: set[str] = set()
    missing_voice_asset_count = 0
    missing_voice_asset_names: list[str] = []
    sfx_used_asset_ids: set[str] = set()
    text_block_count = 0
    total_text_chars = 0
    long_text_block_count = 0
    multiline_text_block_count = 0
    long_text_block_names: list[str] = []
    duplicate_block_id_count = 0
    duplicate_block_id_names: list[str] = []
    missing_block_id_count = 0
    missing_block_id_names: list[str] = []

    for chapter in chapters:
        if not isinstance(chapter, dict):
            continue
        expected, present = count_i18n_translations(chapter, "name", target_i18n_languages)
        if expected:
            i18n_translatable_entry_count += 1
            i18n_expected_translation_count += expected
            i18n_present_translation_count += present

    for scene in scenes:
        expected, present = count_i18n_translations(scene, "name", target_i18n_languages)
        if expected:
            i18n_translatable_entry_count += 1
            i18n_expected_translation_count += expected
            i18n_present_translation_count += present
        blocks = scene.get("blocks") if isinstance(scene.get("blocks"), list) else []
        block_id_counts: dict[str, int] = {}
        block_id_first_indexes: dict[str, int] = {}
        for block_index, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            block_id = str(block.get("id") or "").strip()
            if block_id:
                block_id_counts[block_id] = block_id_counts.get(block_id, 0) + 1
                block_id_first_indexes.setdefault(block_id, block_index)
            else:
                missing_block_id_count += 1
                scene_label = str(scene.get("name") or scene.get("id") or "未命名场景")
                block_type = str(block.get("type") or "unknown").strip() or "unknown"
                missing_block_id_names.append(f"{scene_label}:{block_type}#{block_index + 1}")
        duplicate_block_ids = sorted(block_id for block_id, count in block_id_counts.items() if count > 1)
        duplicate_block_id_count += len(duplicate_block_ids)
        if duplicate_block_ids:
            scene_label = str(scene.get("name") or scene.get("id") or "未命名场景")
            duplicate_block_id_names.extend(f"{scene_label}:{block_id}" for block_id in duplicate_block_ids)
        scene_has_background = False
        scene_has_music = False
        scene_has_effect = False
        for block_index, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "").strip()
            if block_type == "dialogue":
                dialogue_count += 1
                expected, present = count_i18n_translations(block, "text", target_i18n_languages)
                if expected:
                    i18n_translatable_entry_count += 1
                    i18n_expected_translation_count += expected
                    i18n_present_translation_count += present
                speaker_id = str(block.get("speakerId") or "").strip()
                expression_id = str(block.get("expressionId") or "").strip()
                if speaker_id and speaker_id not in characters_by_id:
                    missing_character_ref_count += 1
                    missing_character_ref_names.append(str(block.get("id") or speaker_id))
                elif speaker_id and expression_id and expression_id not in character_expression_ids_by_id.get(speaker_id, set()):
                    missing_expression_ref_count += 1
                    missing_expression_ref_names.append(str(block.get("id") or f"{speaker_id}:{expression_id}"))
                voice_asset_id = str(block.get("voiceAssetId") or "").strip()
                if voice_asset_id:
                    dialogue_voice_count += 1
                    voice_used_asset_ids.add(voice_asset_id)
                    voice_asset = assets_by_id.get(voice_asset_id)
                    if not voice_asset or not get_asset_runtime_path(bundle_dir, voice_asset):
                        missing_voice_asset_count += 1
                        missing_voice_asset_names.append(str(block.get("id") or voice_asset_id))
            elif block_type == "narration":
                narration_count += 1
                expected, present = count_i18n_translations(block, "text", target_i18n_languages)
                if expected:
                    i18n_translatable_entry_count += 1
                    i18n_expected_translation_count += expected
                    i18n_present_translation_count += present
                voice_asset_id = str(block.get("voiceAssetId") or "").strip()
                if voice_asset_id:
                    narration_voice_count += 1
                    voice_used_asset_ids.add(voice_asset_id)
                    voice_asset = assets_by_id.get(voice_asset_id)
                    if not voice_asset or not get_asset_runtime_path(bundle_dir, voice_asset):
                        missing_voice_asset_count += 1
                        missing_voice_asset_names.append(str(block.get("id") or voice_asset_id))
            elif block_type == "choice":
                choice_count += 1
                options = block.get("options") if isinstance(block.get("options"), list) else []
                choice_option_count += len(options)
                if len(options) > 4:
                    crowded_choice_block_count += 1
                seen_choice_texts: set[str] = set()
                plain_target_options: list[str] = []
                for option in options:
                    if not isinstance(option, dict):
                        continue
                    expected, present = count_i18n_translations(option, "text", target_i18n_languages)
                    if expected:
                        i18n_translatable_entry_count += 1
                        i18n_expected_translation_count += expected
                        i18n_present_translation_count += present
                    option_text = str(option.get("text") or "").strip()
                    normalized_option_text = option_text.lower()
                    if not option_text:
                        empty_choice_option_count += 1
                    elif len(option_text) > 42:
                        long_choice_option_count += 1
                    if normalized_option_text:
                        if normalized_option_text in seen_choice_texts:
                            duplicate_choice_option_count += 1
                        seen_choice_texts.add(normalized_option_text)
                    effects = option.get("effects") if isinstance(option.get("effects"), list) else []
                    option_target = str(option.get("gotoSceneId") or option.get("targetSceneId") or "").strip()
                    if option_text and not option_target and not effects:
                        no_action_choice_option_count += 1
                        no_action_choice_option_names.append(str(option.get("id") or option_text))
                    if option_text and option_target and not effects:
                        plain_target_options.append(option_target)
                    for effect in effects:
                        if not isinstance(effect, dict):
                            continue
                        effect_type = str(effect.get("type") or "").strip()
                        if effect_type not in {"variable_set", "variable_add"}:
                            continue
                        choice_effect_count += 1
                        variable_id = str(effect.get("variableId") or "").strip()
                        variable = variables_by_id.get(variable_id)
                        if not variable:
                            logic_missing_variable_count += 1
                        else:
                            variable_written_ids.add(variable_id)
                            if effect_type == "variable_add" and normalize_variable_type(variable.get("type")) != "number":
                                logic_non_number_add_count += 1
                if len(plain_target_options) >= 2 and len(set(plain_target_options)) == 1:
                    same_target_choice_count += 1
                    same_target_choice_names.append(str(block.get("id") or "choice"))
            elif block_type == "variable_set":
                variable_set_count += 1
                variable_id = str(block.get("variableId") or "").strip()
                if variable_id not in variables_by_id:
                    logic_missing_variable_count += 1
                else:
                    variable_written_ids.add(variable_id)
            elif block_type == "variable_add":
                variable_add_count += 1
                variable_id = str(block.get("variableId") or "").strip()
                variable = variables_by_id.get(variable_id)
                if not variable:
                    logic_missing_variable_count += 1
                else:
                    variable_written_ids.add(variable_id)
                    if normalize_variable_type(variable.get("type")) != "number":
                        logic_non_number_add_count += 1
            elif block_type == "condition":
                condition_count += 1
                branches = block.get("branches") if isinstance(block.get("branches"), list) else []
                condition_branch_count += len(branches)
                if not branches:
                    condition_empty_branch_count += 1
                elif not str(block.get("elseGotoSceneId") or "").strip():
                    implicit_condition_fallback_end_count += 1
                    implicit_condition_fallback_names.append(str(block.get("id") or "condition"))
                for branch in branches:
                    if not isinstance(branch, dict):
                        continue
                    if not str(branch.get("gotoSceneId") or "").strip():
                        missing_navigation_target_count += 1
                        missing_navigation_target_names.append(str(branch.get("id") or block.get("id") or "condition_branch"))
                    rules = branch.get("when") if isinstance(branch.get("when"), list) else []
                    condition_rule_count += len(rules)
                    if not rules:
                        condition_empty_branch_count += 1
                    for rule in rules:
                        if not isinstance(rule, dict):
                            continue
                        variable_id = str(rule.get("variableId") or "").strip()
                        variable = variables_by_id.get(variable_id)
                        if not variable:
                            logic_missing_variable_count += 1
                        else:
                            condition_read_variable_ids.add(variable_id)
                            if not condition_operator_matches_variable_type(normalize_variable_type(variable.get("type")), rule.get("operator")):
                                logic_operator_mismatch_count += 1
                conditional_targets = [
                    str(branch.get("gotoSceneId") or "").strip()
                    for branch in branches
                    if isinstance(branch, dict)
                    and str(branch.get("gotoSceneId") or "").strip()
                    and isinstance(branch.get("when"), list)
                    and branch.get("when")
                ]
                if len(conditional_targets) >= 2 and len(set(conditional_targets)) == 1:
                    same_target_condition_count += 1
                    same_target_condition_names.append(str(block.get("id") or "condition"))
            elif block_type == "character_show":
                character_show_count += 1
                character_id = str(block.get("characterId") or "").strip()
                expression_id = str(block.get("expressionId") or "").strip()
                if character_id and character_id not in characters_by_id:
                    missing_character_ref_count += 1
                    missing_character_ref_names.append(str(block.get("id") or character_id))
                elif character_id and expression_id and expression_id not in character_expression_ids_by_id.get(character_id, set()):
                    missing_expression_ref_count += 1
                    missing_expression_ref_names.append(str(block.get("id") or f"{character_id}:{expression_id}"))
                character_position_values.add(str(block.get("position") or "center").strip() or "center")
                if get_safe_character_transition(block.get("transition")) != "none" and get_safe_transition_duration_ms(block.get("transitionDurationMs"), 600) > 0:
                    character_transition_count += 1
                stage = get_safe_character_stage(block.get("stage") if isinstance(block.get("stage"), dict) else None)
                if (
                    stage.get("offsetX") != 0
                    or stage.get("offsetY") != 0
                    or stage.get("scale") != 100
                    or stage.get("opacity") != 100
                    or stage.get("layer") != 0
                    or stage.get("flipX")
                ):
                    character_stage_adjustment_count += 1
            elif block_type == "character_move":
                character_move_count += 1
                character_id = str(block.get("characterId") or "").strip()
                expression_id = str(block.get("expressionId") or "").strip()
                if character_id and character_id not in characters_by_id:
                    missing_character_ref_count += 1
                    missing_character_ref_names.append(str(block.get("id") or character_id))
                elif character_id and expression_id and expression_id not in character_expression_ids_by_id.get(character_id, set()):
                    missing_expression_ref_count += 1
                    missing_expression_ref_names.append(str(block.get("id") or f"{character_id}:{expression_id}"))
                character_position_values.add(str(block.get("position") or "center").strip() or "center")
                stage = get_safe_character_stage(block.get("stage") if isinstance(block.get("stage"), dict) else None)
                if (
                    stage.get("offsetX") != 0
                    or stage.get("offsetY") != 0
                    or stage.get("scale") != 100
                    or stage.get("opacity") != 100
                    or stage.get("layer") != 0
                    or stage.get("flipX")
                ):
                    character_stage_adjustment_count += 1
            elif block_type == "character_hide":
                character_hide_count += 1
                character_id = str(block.get("characterId") or "").strip()
                if character_id and character_id not in characters_by_id:
                    missing_character_ref_count += 1
                    missing_character_ref_names.append(str(block.get("id") or character_id))
                if get_safe_character_transition(block.get("transition")) != "none" and get_safe_transition_duration_ms(block.get("transitionDurationMs"), 600) > 0:
                    character_transition_count += 1
            elif block_type == "jump":
                if not str(block.get("targetSceneId") or "").strip():
                    missing_navigation_target_count += 1
                    missing_navigation_target_names.append(str(block.get("id") or "jump"))
            elif block_type == "background":
                scene_has_background = True
                background_block_count += 1
                background_asset_id = str(block.get("assetId") or "").strip()
                if background_asset_id:
                    background_asset_ids.add(background_asset_id)
                background_asset = assets_by_id.get(background_asset_id) if background_asset_id else None
                if not background_asset or not get_asset_runtime_path(bundle_dir, background_asset):
                    missing_background_asset_count += 1
                    missing_background_asset_names.append(str(block.get("id") or background_asset_id or "未命名背景卡"))
                elif background_asset.get("type") == "cg":
                    cg_used_asset_ids.add(background_asset_id)
                if get_safe_basic_transition(block.get("transition")) != "none" and get_safe_transition_duration_ms(block.get("transitionDurationMs"), 600) > 0:
                    background_transition_count += 1
            elif block_type == "music_play":
                scene_has_music = True
                music_play_count += 1
                music_asset_id = str(block.get("assetId") or "").strip()
                if music_asset_id:
                    music_used_asset_ids.add(music_asset_id)
                music_asset = assets_by_id.get(music_asset_id) if music_asset_id else None
                if not music_asset or not get_asset_runtime_path(bundle_dir, music_asset):
                    missing_music_asset_count += 1
                    missing_music_asset_names.append(str(block.get("id") or music_asset_id or "未命名音乐卡"))
                if get_safe_audio_fade_ms(block.get("fadeInMs"), 0) > 0:
                    music_fade_in_count += 1
                if get_safe_audio_fade_ms(block.get("fadeOutMs"), 0) > 0:
                    music_fade_out_count += 1
                if get_safe_music_end_mode(block.get("endMode")) != "until_next_music":
                    music_scoped_count += 1
                if get_safe_music_end_mode(block.get("endMode")) == "after_block":
                    music_after_block_scope_count += 1
                    end_block_id = str(block.get("endBlockId") or "").strip()
                    block_label = str(block.get("id") or music_asset_id or "未命名音乐卡")
                    scene_label = str(scene.get("name") or scene.get("id") or "未命名场景")
                    if not end_block_id or end_block_id not in block_id_first_indexes:
                        missing_music_end_block_count += 1
                        missing_music_end_block_names.append(f"{scene_label}:{block_label}->{end_block_id or '未设置'}")
                    elif block_id_first_indexes[end_block_id] <= block_index:
                        backward_music_end_block_count += 1
                        backward_music_end_block_names.append(f"{scene_label}:{block_label}->{end_block_id}")
            elif block_type == "music_stop":
                music_stop_count += 1
                if get_safe_audio_fade_ms(block.get("fadeOutMs"), 0) > 0:
                    music_fade_out_count += 1
            elif block_type == "sfx_play":
                sfx_play_count += 1
                sfx_asset_id = str(block.get("assetId") or "").strip()
                if sfx_asset_id:
                    sfx_used_asset_ids.add(sfx_asset_id)
                sfx_asset = assets_by_id.get(sfx_asset_id) if sfx_asset_id else None
                if not sfx_asset or not get_asset_runtime_path(bundle_dir, sfx_asset):
                    missing_sfx_asset_count += 1
                    missing_sfx_asset_names.append(str(block.get("id") or sfx_asset_id or "未命名音效卡"))
            elif block_type == "video_play":
                video_play_count += 1
                video_asset_id = str(block.get("assetId") or "").strip()
                video_asset = assets_by_id.get(video_asset_id) if video_asset_id else None
                if not video_asset or not get_asset_runtime_path(bundle_dir, video_asset):
                    missing_video_asset_count += 1
                    missing_video_asset_names.append(str(block.get("id") or video_asset_id or "未命名视频卡"))
            elif block_type == "credits_roll":
                credits_roll_count += 1
                lines = block.get("lines") if isinstance(block.get("lines"), list) else []
                non_empty_lines = [str(line).strip() for line in lines if str(line).strip()]
                credits_line_count += len(non_empty_lines)
                if not str(block.get("title") or "").strip() and not str(block.get("subtitle") or "").strip() and not non_empty_lines:
                    empty_credits_roll_count += 1
                try:
                    credits_duration_seconds = float(block.get("durationSeconds") or 0)
                except (TypeError, ValueError):
                    credits_duration_seconds = 0.0
                if credits_duration_seconds < 4:
                    short_credits_roll_count += 1
                    short_credits_roll_names.append(str(block.get("id") or block.get("title") or "未命名片尾字幕"))
            elif block_type in VN_BASELINE_EFFECT_BLOCK_TYPES:
                scene_has_effect = True
            text = get_vn_baseline_block_text(block)
            if block_type in {"dialogue", "narration", "choice"}:
                text_block_count += 1
                total_text_chars += len(text)
                if not text:
                    empty_text_count += 1
                if block_type in {"dialogue", "narration"}:
                    if len(text) > VN_TEXT_LONG_WARNING_LENGTH:
                        long_text_block_count += 1
                        long_text_block_names.append(str(block.get("id") or block_type))
                    if text.count("\n") >= VN_TEXT_LONG_WARNING_LINES:
                        multiline_text_block_count += 1
        if scene_has_background:
            scenes_with_background += 1
        if scene_has_music:
            scenes_with_music += 1
        if scene_has_effect:
            scenes_with_effects += 1

    characters_with_sprite = 0
    characters_missing_sprite = []
    for character in characters:
        if not isinstance(character, dict):
            continue
        asset_id = get_vn_baseline_character_sprite_asset_id(character)
        asset = assets_by_id.get(asset_id) if asset_id else None
        if asset_id and asset and get_asset_runtime_path(bundle_dir, asset):
            characters_with_sprite += 1
        else:
            characters_missing_sprite.append(str(character.get("displayName") or character.get("name") or character.get("id") or "未命名角色"))

    placeholder_assets = [
        str(asset.get("name") or asset.get("id") or "未命名素材")
        for asset in assets
        if isinstance(asset, dict) and is_vn_baseline_placeholder_asset(asset)
    ]
    unused_cg_asset_ids = sorted(cg_asset_ids - cg_used_asset_ids)
    unused_cg_asset_names = [
        str((assets_by_id.get(asset_id) or {}).get("name") or asset_id)
        for asset_id in unused_cg_asset_ids
    ]
    unused_bgm_asset_ids = sorted(bgm_asset_ids - music_used_asset_ids)
    unused_bgm_asset_names = [
        str((assets_by_id.get(asset_id) or {}).get("name") or asset_id)
        for asset_id in unused_bgm_asset_ids
    ]
    unused_sfx_asset_ids = sorted(sfx_asset_ids - sfx_used_asset_ids)
    unused_sfx_asset_names = [
        str((assets_by_id.get(asset_id) or {}).get("name") or asset_id)
        for asset_id in unused_sfx_asset_ids
    ]
    unused_voice_asset_ids = sorted(voice_asset_ids - voice_used_asset_ids)
    unused_voice_asset_names = [
        str((assets_by_id.get(asset_id) or {}).get("name") or asset_id)
        for asset_id in unused_voice_asset_ids
    ]
    route_influencing_variable_ids = sorted(variable_written_ids & condition_read_variable_ids)
    unconsumed_variable_write_ids = sorted(variable_written_ids - condition_read_variable_ids)
    unconsumed_variable_write_names = [
        str((variables_by_id.get(variable_id) or {}).get("name") or variable_id)
        for variable_id in unconsumed_variable_write_ids
    ]
    scene_count = len(scenes)
    text_density = round(text_block_count / scene_count, 2) if scene_count else 0.0
    average_text_length = round(total_text_chars / text_block_count, 1) if text_block_count else 0.0
    dialog_box_background_opacity = int(dialog_box_config.get("backgroundOpacity") or 0)
    dialog_box_panel_asset_opacity = int(dialog_box_config.get("panelAssetOpacity") or 0)
    dialog_box_has_panel_art = bool(str(dialog_box_config.get("panelAssetId") or "").strip() and dialog_box_panel_asset_opacity >= 35)
    dialog_box_text_contrast_ratio = get_vn_baseline_color_contrast_ratio(
        dialog_box_config.get("textColor"),
        dialog_box_config.get("backgroundColor"),
    )
    dialog_box_readability_notes: list[str] = []
    if text_block_count >= 3:
        if dialog_box_background_opacity < 45 and not dialog_box_has_panel_art:
            dialog_box_readability_notes.append(f"背景不透明度仅 {dialog_box_background_opacity}% 且没有高透明度面板图")
        if dialog_box_text_contrast_ratio < 4.5 and (dialog_box_background_opacity >= 45 or dialog_box_has_panel_art):
            dialog_box_readability_notes.append(f"正文与文本框底色对比约 {dialog_box_text_contrast_ratio}:1")
        if int(dialog_box_config.get("widthPercent") or 0) < 64:
            dialog_box_readability_notes.append(f"文本框宽度仅 {int(dialog_box_config.get('widthPercent') or 0)}%")
        if int(dialog_box_config.get("minHeight") or 0) < 118 and (average_text_length >= 32 or long_text_block_count or multiline_text_block_count):
            dialog_box_readability_notes.append(f"文本框最小高度仅 {int(dialog_box_config.get('minHeight') or 0)}px")
        if int(dialog_box_config.get("paddingX") or 0) < 12 or int(dialog_box_config.get("paddingY") or 0) < 8:
            dialog_box_readability_notes.append(
                f"文本内边距偏小（{int(dialog_box_config.get('paddingX') or 0)} / {int(dialog_box_config.get('paddingY') or 0)}）"
            )
    dialog_box_readability_risk_count = len(dialog_box_readability_notes)
    voice_eligible_line_count = dialogue_count + narration_count
    voice_bound_line_count = dialogue_voice_count + narration_voice_count
    voice_coverage_percent = round(voice_bound_line_count / voice_eligible_line_count * 100, 1) if voice_eligible_line_count else 0.0
    i18n_translation_coverage_percent = (
        round(i18n_present_translation_count / i18n_expected_translation_count * 100, 1)
        if i18n_expected_translation_count
        else (100.0 if not target_i18n_languages else 0.0)
    )
    missing_route_targets: list[str] = []
    scene_outgoing_targets: dict[str, list[str]] = {}
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("id") or "").strip()
        if not scene_id:
            continue
        targets = collect_scene_outgoing_targets(scene)
        scene_outgoing_targets[scene_id] = targets
        for target in targets:
            if target not in valid_scene_ids:
                missing_route_targets.append(f"{scene_id}->{target}")
    reachable_scene_ids: set[str] = set()
    if entry_scene_id in valid_scene_ids:
        pending_scene_ids = [entry_scene_id]
        while pending_scene_ids:
            scene_id = pending_scene_ids.pop(0)
            if scene_id in reachable_scene_ids:
                continue
            reachable_scene_ids.add(scene_id)
            for target in scene_outgoing_targets.get(scene_id, []):
                if target in valid_scene_ids and target not in reachable_scene_ids:
                    pending_scene_ids.append(target)
    unreachable_scene_ids = sorted(valid_scene_ids - reachable_scene_ids) if reachable_scene_ids else []
    ending_scene_count = len(build_ending_scene_ids(chapters))
    reachable_terminal_scene_names: list[str] = []
    reachable_plain_terminal_scene_names: list[str] = []
    reachable_terminal_scene_count = 0
    reachable_credits_terminal_scene_count = 0
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("id") or "").strip()
        if not scene_id or (reachable_scene_ids and scene_id not in reachable_scene_ids):
            continue
        if scene_outgoing_targets.get(scene_id):
            continue
        reachable_terminal_scene_count += 1
        scene_name = str(scene.get("name") or scene_id)
        reachable_terminal_scene_names.append(scene_name)
        blocks = scene.get("blocks") if isinstance(scene.get("blocks"), list) else []
        has_credits_roll = any(
            isinstance(block, dict) and str(block.get("type") or "").strip() == "credits_roll"
            for block in blocks
        )
        if has_credits_roll:
            reachable_credits_terminal_scene_count += 1
        else:
            reachable_plain_terminal_scene_names.append(scene_name)
    issues: list[dict] = []

    if not scenes:
        add_vn_baseline_issue(
            issues,
            "warn",
            "no_story_scene",
            "没有可试玩场景",
            "导出包里没有检测到章节场景。",
            "至少创建一个章节和入口场景，再重新导出原生 Runtime 包。",
        )
    if duplicate_chapter_ids:
        add_vn_baseline_issue(
            issues,
            "warn",
            "duplicate_chapter_id",
            "章节 ID 存在重复",
            f"检测到 {len(duplicate_chapter_ids)} 个重复章节 ID：{', '.join(duplicate_chapter_ids[:3])}",
            "复制章节后请重新生成或修改章节 ID；重复 ID 会影响章节回放、发布报告和后续迁移工具识别章节。",
        )
    if missing_scene_id_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "missing_scene_id",
            "存在没有 ID 的场景",
            f"检测到 {missing_scene_id_count} 个场景没有 ID：{', '.join(missing_scene_id_names[:3])}",
            "为每个场景生成稳定 ID；缺失场景 ID 会影响入口、跳转、存档、章节回放和结局解锁定位。",
        )
    if missing_block_id_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "missing_block_id",
            "存在没有 ID 的剧情卡片",
            f"检测到 {missing_block_id_count} 张剧情卡片没有 ID：{', '.join(missing_block_id_names[:3])}",
            "为每张卡片生成稳定 ID；缺失卡片 ID 会影响文本历史、语音回听、BGM after_block 范围和后续自动化迁移。",
        )
    if empty_chapter_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "empty_chapter",
            "存在没有场景的空章节",
            f"检测到 {empty_chapter_count} 个空章节：{', '.join(empty_chapter_names[:3])}",
            "如果只是草稿章节，建议发布前隐藏、补场景或移出发布包；否则章节回放里会像半成品入口。",
        )
    if scenes and entry_scene_id not in valid_scene_ids:
        add_vn_baseline_issue(
            issues,
            "warn",
            "entry_scene_missing",
            "入口场景不可用",
            f"项目入口场景指向 {entry_scene_id or '空值'}，但导出包里没有这个场景。",
            "在项目设置里重新指定存在的入口场景，避免玩家启动原生 Runtime 后直接掉到异常或错误章节。",
        )
    if missing_route_targets:
        add_vn_baseline_issue(
            issues,
            "warn",
            "route_target_missing",
            "路线跳转目标缺失",
            f"检测到 {len(missing_route_targets)} 个跳转目标不存在：{', '.join(missing_route_targets[:3])}",
            "检查选项、条件分支和跳转卡片，确保每个目标场景都存在；删除场景后尤其要重新巡检路线。",
        )
    if missing_navigation_target_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "navigation_target_empty",
            "路线控制卡片缺少跳转目标",
            f"检测到 {missing_navigation_target_count} 个跳转或条件分支没有目标场景：{', '.join(missing_navigation_target_names[:3])}",
            "补齐目标场景，或改成明确的结局/片尾卡片；否则原生 Runtime 会把空目标视为剧情结束，玩家可能以为流程断了。",
        )
    if implicit_condition_fallback_end_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "condition_fallback_implicit_end",
            "条件未命中时会隐式结束",
            f"检测到 {implicit_condition_fallback_end_count} 个条件卡片没有设置未命中目标：{', '.join(implicit_condition_fallback_names[:3])}",
            "如果未命中条件就是结局，建议接到明确的结局或片尾场景；如果只是兜底分支遗漏，请补 else 目标场景。",
        )
    if unreachable_scene_ids:
        add_vn_baseline_issue(
            issues,
            "soft",
            "unreachable_scene",
            "存在入口无法到达的场景",
            f"从入口场景出发，有 {len(unreachable_scene_ids)} 个场景没有被路线连接：{', '.join(unreachable_scene_ids[:3])}",
            "如果这些是正式内容，请用选项、跳转或条件分支接入；如果只是素材草稿，建议标记或移出发布章节。",
        )
    if scene_count >= 2 and reachable_plain_terminal_scene_names:
        add_vn_baseline_issue(
            issues,
            "soft",
            "plain_terminal_scene",
            "部分可达路线缺少明确收束",
            f"检测到 {len(reachable_plain_terminal_scene_names)} 个入口可到达的终点场景没有片尾字幕卡片：{', '.join(reachable_plain_terminal_scene_names[:3])}",
            "如果这是正式结局，建议补片尾字幕、结局说明或明确的收束场景；如果只是中途断点，请接回后续场景，避免玩家以为流程坏了。",
        )
    if placeholder_assets:
        add_vn_baseline_issue(
            issues,
            "warn",
            "placeholder_assets",
            "仍有占位素材",
            f"检测到 {len(placeholder_assets)} 个疑似占位素材：{', '.join(placeholder_assets[:3])}",
            "发布前替换占位图、占位音频或临时 UI，避免玩家打开后误以为是半成品。",
        )
    if empty_text_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "empty_story_text",
            "存在空白剧情文本",
            f"检测到 {empty_text_count} 个台词、旁白或选项没有正文。",
            "回到剧情编辑器补齐文本，或删除不再需要的空卡片。",
        )
    if missing_voice_asset_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "voice_asset_missing",
            "存在已绑定但缺失的语音文件",
            f"检测到 {missing_voice_asset_count} 条台词/旁白绑定了语音，但文件没有进入原生包：{', '.join(missing_voice_asset_names[:3])}",
            "重新导入或替换缺失语音素材，再导出原生 Runtime，避免玩家点开后听不到应有配音。",
        )
    if missing_music_asset_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "bgm_asset_missing",
            "存在缺失的 BGM 文件",
            f"检测到 {missing_music_asset_count} 张 BGM 播放卡片没有可用文件：{', '.join(missing_music_asset_names[:3])}",
            "重新导入或替换缺失 BGM 素材，再导出原生 Runtime，避免章节开头、情绪段落或切歌点静默失效。",
        )
    if missing_background_asset_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "background_asset_missing",
            "存在缺失的背景/CG 文件",
            f"检测到 {missing_background_asset_count} 张背景卡片没有可用文件：{', '.join(missing_background_asset_names[:3])}",
            "重新导入或替换缺失背景、CG 或 3D 场景素材，再导出原生 Runtime，避免试玩中出现黑屏或占位背景。",
        )
    if missing_sfx_asset_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "sfx_asset_missing",
            "存在缺失的音效文件",
            f"检测到 {missing_sfx_asset_count} 张音效卡片没有可用文件：{', '.join(missing_sfx_asset_names[:3])}",
            "重新导入或替换缺失音效素材，再导出原生 Runtime，避免点击、脚步或演出音效静默失效。",
        )
    if missing_video_asset_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "video_asset_missing",
            "存在缺失的视频文件",
            f"检测到 {missing_video_asset_count} 张视频播放卡片没有可用文件：{', '.join(missing_video_asset_names[:3])}",
            "重新导入或替换缺失 OP、ED、PV 或过场视频素材，再导出原生 Runtime，避免玩家点击播放后只看到占位提示。",
        )
    if empty_credits_roll_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "credits_empty",
            "片尾字幕内容为空",
            f"检测到 {empty_credits_roll_count} 张片尾字幕卡片没有标题、副标题或字幕行。",
            "补齐 STAFF、感谢名单或制作信息；如果暂时不需要片尾，请删除空片尾字幕卡片，避免玩家看到空白收尾。",
        )
    if short_credits_roll_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "credits_duration_short",
            "片尾字幕时长过短",
            f"检测到 {short_credits_roll_count} 张片尾字幕低于 4 秒：{', '.join(short_credits_roll_names[:3])}",
            "将片尾字幕时长调到 8-30 秒，确保 STAFF 和感谢信息能被正常读完。",
        )
    if empty_choice_option_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "empty_choice_option",
            "存在空白选项按钮",
            f"检测到 {empty_choice_option_count} 个选项按钮没有文案。",
            "补齐选项文案或删除空选项，避免玩家在原生 Runtime 里看到空白按钮。",
        )
    if no_action_choice_option_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "choice_option_no_action",
            "部分选项没有明确动作",
            f"检测到 {no_action_choice_option_count} 个选项既没有跳转目标，也没有变量效果：{', '.join(no_action_choice_option_names[:3])}",
            "如果这是“继续当前剧情”的设计，建议至少加一个变量记录或后续差分；否则请补跳转目标，避免玩家以为选项是假按钮。",
        )
    if same_target_choice_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "choice_same_target",
            "部分选项分支结果完全相同",
            f"检测到 {same_target_choice_count} 个选项卡的多个按钮都跳到同一个场景且没有变量效果：{', '.join(same_target_choice_names[:3])}",
            "如果这是有意设计，建议至少加变量记录、好感度变化或后续差分；否则请拆出不同目标，避免玩家觉得选项只是装饰。",
        )
    if same_target_condition_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "condition_same_target",
            "部分条件分支结果完全相同",
            f"检测到 {same_target_condition_count} 个条件卡的多个有效分支都跳到同一个场景：{', '.join(same_target_condition_names[:3])}",
            "如果这是共通收束，请确认变量变化会在后续产生差分；否则建议把不同条件接到不同场景，避免条件分支看起来只是装饰。",
        )
    if target_i18n_languages and fallback_language not in supported_languages:
        add_vn_baseline_issue(
            issues,
            "warn",
            "i18n_fallback_not_supported",
            "多语言 fallback 不在支持语言列表中",
            f"fallbackLanguage={fallback_language}，但 supportedLanguages={', '.join(supported_languages)}。",
            "把 fallbackLanguage 加入支持语言列表，或改成默认语言；否则 Runtime 切换语言时可能只能退回原文。",
        )
    if target_i18n_languages and i18n_expected_translation_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "i18n_enabled_without_translations",
            "已开启多语言但没有检测到剧情翻译",
            f"当前支持 {len(supported_languages)} 种语言：{', '.join(supported_languages)}，但章节、场景、角色、台词和选项没有目标语言翻译。",
            "如果要对外宣传多语言，建议先补主线文本和选项翻译；如果只是预留功能，可以暂时只保留默认语言。",
        )
    elif target_i18n_languages and i18n_translation_coverage_percent < 60:
        add_vn_baseline_issue(
            issues,
            "soft",
            "i18n_translation_sparse",
            "多语言翻译覆盖偏低",
            f"目标语言翻译覆盖约 {i18n_translation_coverage_percent}%（{i18n_present_translation_count}/{i18n_expected_translation_count}）。",
            "优先补齐章节名、场景名、选项和主线对白；否则玩家切换语言后会频繁看到默认语言文本。",
        )
    if duplicate_variable_ids:
        add_vn_baseline_issue(
            issues,
            "warn",
            "logic_variable_duplicate_id",
            "变量 ID 存在重复",
            f"检测到 {len(duplicate_variable_ids)} 个重复变量 ID：{', '.join(sorted(duplicate_variable_ids)[:3])}",
            "回到变量库合并或重命名重复变量，避免条件分支、选项效果和存档摘要读到不可预测的值。",
        )
    if duplicate_scene_ids:
        add_vn_baseline_issue(
            issues,
            "warn",
            "duplicate_scene_id",
            "场景 ID 存在重复",
            f"检测到 {len(duplicate_scene_ids)} 个重复场景 ID：{', '.join(duplicate_scene_ids[:3])}",
            "复制场景后请重新生成或修改场景 ID；重复 ID 会让跳转、可达性分析和存档定位变得不可预测。",
        )
    if duplicate_block_id_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "duplicate_block_id",
            "同一场景内存在重复卡片 ID",
            f"检测到 {duplicate_block_id_count} 个重复卡片 ID：{', '.join(duplicate_block_id_names[:3])}",
            "复制卡片后请重新生成或修改卡片 ID；重复 ID 会影响 BGM 结束范围、文本历史、语音回听和自动化发布检查。",
        )
    if duplicate_asset_ids:
        add_vn_baseline_issue(
            issues,
            "warn",
            "duplicate_asset_id",
            "素材 ID 存在重复",
            f"检测到 {len(duplicate_asset_ids)} 个重复素材 ID：{', '.join(duplicate_asset_ids[:3])}",
            "重新导入或重命名重复素材；重复 ID 会让背景、BGM、语音、字体、3D 模型等引用指向不可预测的文件。",
        )
    if duplicate_character_ids:
        add_vn_baseline_issue(
            issues,
            "warn",
            "duplicate_character_id",
            "角色 ID 存在重复",
            f"检测到 {len(duplicate_character_ids)} 个重复角色 ID：{', '.join(duplicate_character_ids[:3])}",
            "合并或重命名重复角色；重复 ID 会让说话人、立绘登场、回想馆和角色资料索引互相覆盖。",
        )
    if duplicate_expression_id_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "duplicate_expression_id",
            "同一角色内存在重复表情 ID",
            f"检测到 {duplicate_expression_id_count} 个重复表情 ID：{', '.join(duplicate_expression_id_names[:3])}",
            "为同一角色的每个表情使用唯一 ID；重复 ID 会让表情差分和 Live2D / 3D 兜底映射显示错表情。",
        )
    if font_status["fontAssetMissingCount"]:
        add_vn_baseline_issue(
            issues,
            "warn",
            "font_asset_missing",
            "项目字体素材不可用",
            "；".join(font_status["fontIssueNotes"][:3]) + "。",
            "重新导入字体文件、重新选择字体素材，或清空字体绑定改用系统字体；否则玩家机器上可能回退到默认字体。",
        )
    elif font_status["fontAssetTypeRiskCount"]:
        add_vn_baseline_issue(
            issues,
            "soft",
            "font_asset_type_risk",
            "项目字体素材类型不匹配",
            "；".join(font_status["fontIssueNotes"][:3]) + "。",
            "字体素材建议通过 font 类型导入，避免素材库整理、导出筛选和授权检查时被当作普通文件。",
        )
    elif font_status["fontExtensionRiskCount"]:
        add_vn_baseline_issue(
            issues,
            "soft",
            "font_extension_risk",
            "项目字体格式可能不稳定",
            "；".join(font_status["fontIssueNotes"][:3]) + "。",
            "建议使用 ttf、otf 或 ttc，并确认字体授权允许随游戏分发；不推荐格式可能在部分平台无法加载。",
        )
    if logic_missing_variable_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "logic_variable_missing",
            "逻辑卡片引用了不存在的变量",
            f"检测到 {logic_missing_variable_count} 处变量设置、条件判断或选项效果引用了缺失变量。",
            "重新选择变量或先在变量库创建对应变量；否则原生 Runtime 会跳过这些逻辑，分支状态可能失效。",
        )
    if logic_non_number_add_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "logic_variable_add_type",
            "数字加减绑定了非数字变量",
            f"检测到 {logic_non_number_add_count} 处变量加减或选项加减效果没有绑定数字变量。",
            "把变量加减改绑到 number 类型变量，或改用变量设置效果；否则 Runtime 会忽略这类变化。",
        )
    if logic_operator_mismatch_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "logic_condition_operator",
            "条件比较方式和变量类型不匹配",
            f"检测到 {logic_operator_mismatch_count} 条条件规则使用了不适合当前变量类型的比较符。",
            "文本和开关变量只用等于/不等于；大于、小于这类比较请改用数字变量。",
        )
    if unconsumed_variable_write_ids and (condition_count or choice_effect_count or variable_set_count or variable_add_count):
        add_vn_baseline_issue(
            issues,
            "soft",
            "logic_variable_unconsumed_write",
            "部分变量变化没有进入路线判断",
            f"检测到 {len(unconsumed_variable_write_ids)} 个被写入但没有被条件分支读取的变量：{', '.join(unconsumed_variable_write_names[:3])}",
            "如果这些变量代表好感度、路线旗标或状态差分，建议补条件分支读取它们；如果只是成就、统计或存档展示变量，可以在发布说明里明确用途。",
        )
    if characters and characters_with_sprite < len(characters):
        add_vn_baseline_issue(
            issues,
            "warn",
            "character_fallback_sprite",
            "角色缺少可用立绘兜底",
            f"{len(characters) - characters_with_sprite} 个角色没有可用立绘文件：{', '.join(characters_missing_sprite[:3])}",
            "即使使用 Live2D / 3D，也建议给每个角色绑定一张兜底立绘，降低目标机器不支持模型时的翻车风险。",
        )
    if missing_character_ref_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "character_reference_missing",
            "剧情卡片引用了不存在的角色",
            f"检测到 {missing_character_ref_count} 处台词、角色出场或退场引用了缺失角色：{', '.join(missing_character_ref_names[:3])}",
            "回到剧情编辑器重新选择说话人或出场角色；删除角色后尤其要跑一次发布检查，避免原生 Runtime 只显示空名或占位人物。",
        )
    if missing_expression_ref_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "character_expression_missing",
            "剧情卡片引用了不存在的表情",
            f"检测到 {missing_expression_ref_count} 处台词或角色出场引用了缺失表情：{', '.join(missing_expression_ref_names[:3])}",
            "重新选择角色表情，或在角色资料里补回对应表情；否则 Runtime 会回退默认外观，关键表情差分会丢失。",
        )
    if scene_count and scenes_with_background < scene_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "background_coverage",
            "背景覆盖不完整",
            f"{scene_count - scenes_with_background} 个场景没有背景卡片。",
            "给每个可试玩场景至少放一张背景、CG 或 3D 场景，避免黑屏式试玩体验。",
        )
    if background_block_count >= 2 and len(background_asset_ids) >= 2 and background_transition_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "background_transition_missing",
            "背景切换缺少基础转场",
            f"检测到 {background_block_count} 张背景卡片、{len(background_asset_ids)} 个背景素材，但没有淡入淡出转场。",
            "给章节开头或场景切换设置 400-1000ms 的淡入淡出，避免背景硬切影响沉浸感。",
        )
    expected_music_scenes = max(1, math.ceil(scene_count * 0.6)) if scene_count else 0
    if scene_count and scenes_with_music < expected_music_scenes:
        add_vn_baseline_issue(
            issues,
            "soft",
            "bgm_plan",
            "BGM 规划偏少",
            f"当前 {scene_count} 个场景里只有 {scenes_with_music} 个场景主动播放 BGM。",
            "为章节开头、转场或情绪段落设置 BGM 范围；短篇也建议至少有一条明确的音乐进入点。",
        )
    if music_play_count >= 2 and music_scoped_count == 0 and music_stop_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "bgm_scope",
            "多首 BGM 缺少明确范围",
            f"检测到 {music_play_count} 个 BGM 播放点，但没有 scene_end / after_block 范围或停止音乐卡片。",
            "给关键曲目设置结束范围，或在段落末尾补停止音乐卡片，避免音乐覆盖到不该出现的场景。",
        )
    if missing_music_end_block_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "bgm_after_block_target_missing",
            "BGM after_block 结束卡片不可用",
            f"检测到 {missing_music_end_block_count} 个 BGM 范围指向不存在的结束卡片：{', '.join(missing_music_end_block_names[:3])}",
            "重新选择同一场景内存在的结束卡片；否则这段 BGM 的自定义范围不会按预期停止。",
        )
    if backward_music_end_block_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "bgm_after_block_target_before_play",
            "BGM after_block 结束点早于播放点",
            f"检测到 {backward_music_end_block_count} 个 BGM 范围结束点位于播放卡片之前：{', '.join(backward_music_end_block_names[:3])}",
            "把结束卡片放到音乐播放卡片之后，或改用 scene_end / until_next_music；否则音乐可能刚播放就结束。",
        )
    if music_play_count and music_fade_in_count < music_play_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "bgm_fade_in",
            "部分 BGM 没有淡入",
            f"{music_play_count - music_fade_in_count} 个 BGM 播放点没有设置淡入时间。",
            "给 BGM 播放卡片设置 400-1000ms 的淡入，减少切歌突兀感。",
        )
    if music_stop_count and music_fade_out_count < music_stop_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "bgm_fade_out",
            "部分 BGM 没有淡出",
            f"{music_stop_count - music_fade_out_count} 个停止音乐卡片没有设置淡出时间。",
            "给停止音乐卡片设置淡出，让场景切换和静音段落更自然。",
        )
    if voice_bound_line_count and voice_eligible_line_count >= 5 and voice_coverage_percent < 70:
        add_vn_baseline_issue(
            issues,
            "soft",
            "voice_coverage_gap",
            "语音覆盖存在明显断层",
            f"当前 {voice_eligible_line_count} 条台词/旁白里有 {voice_bound_line_count} 条绑定语音，覆盖约 {voice_coverage_percent}%。",
            "如果这是配音试玩版，建议集中补齐主线关键句，或暂时移除零散语音，避免玩家误以为漏配。",
        )
    if scene_count >= 2 and choice_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "choice_node",
            "缺少可交互选项",
            "多场景项目没有检测到选项节点。",
            "如果目标是视觉小说而非纯电子书，建议至少加入一个选项、分支或可回收差分。",
        )
    if long_choice_option_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "long_choice_option",
            "部分选项文案偏长",
            f"检测到 {long_choice_option_count} 个选项超过 42 字。",
            "把选项按钮压缩成玩家一眼能读完的行动意图，详细心理活动可以放进下一句旁白。",
        )
    if duplicate_choice_option_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "duplicate_choice_option",
            "同组选项存在重复文案",
            f"检测到 {duplicate_choice_option_count} 个重复选项文案。",
            "给每个选项写出明确差异，避免玩家以为分支无效或按钮重复。",
        )
    if crowded_choice_block_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "crowded_choice_block",
            "选项按钮数量偏多",
            f"检测到 {crowded_choice_block_count} 个选项卡片超过 4 个按钮。",
            "如果不是菜单式选择，建议拆成两层选择或减少同屏按钮数量，提升手柄/键盘选择体验。",
        )
    if condition_empty_branch_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "logic_condition_empty",
            "条件分支规则不完整",
            f"检测到 {condition_empty_branch_count} 个条件分支没有分支或没有规则。",
            "补齐条件规则，或确认这些分支就是默认兜底逻辑；发布前最好避免看起来像半成品的空条件。",
        )
    if scene_count >= 3 and sfx_play_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "sfx_plan",
            "缺少基础音效点",
            "多场景项目没有检测到播放音效卡片。",
            "为门铃、脚步、点击、心跳、短信提示或关键演出补少量音效点，能显著提升试玩完成度。",
        )
    if video_asset_count and video_play_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "video_asset_unused",
            "视频素材还没有进入剧情",
            f"检测到 {video_asset_count} 个视频素材，但没有播放视频卡片。",
            "如果这些是 OP、ED、PV 或过场动画，建议放入对应章节并跑一次原生 Runtime 视频桥接检查。",
        )
    if unused_cg_asset_ids:
        add_vn_baseline_issue(
            issues,
            "soft",
            "cg_asset_unused",
            "部分 CG 素材还没有进入剧情",
            f"检测到 {len(unused_cg_asset_ids)} 张 CG 素材没有被背景/CG 卡引用：{', '.join(unused_cg_asset_names[:3])}",
            "把正式 CG 放进对应场景，或先移出发布包；否则 CG 回想馆会缺少可解锁内容，看起来像功能没有做完。",
        )
    if unused_bgm_asset_ids:
        add_vn_baseline_issue(
            issues,
            "soft",
            "bgm_asset_unused",
            "部分 BGM 素材还没有进入剧情",
            f"检测到 {len(unused_bgm_asset_ids)} 首 BGM 没有被播放卡引用：{', '.join(unused_bgm_asset_names[:3])}",
            "把正式曲目放进对应章节或先移出发布包；否则音乐鉴赏和发布包体都会显得没有整理干净。",
        )
    if unused_sfx_asset_ids:
        add_vn_baseline_issue(
            issues,
            "soft",
            "sfx_asset_unused",
            "部分音效素材还没有进入剧情",
            f"检测到 {len(unused_sfx_asset_ids)} 个音效没有被播放卡引用：{', '.join(unused_sfx_asset_names[:3])}",
            "把正式音效放到点击、脚步、门铃或关键演出点；如果只是临时素材，发布前建议移出包体。",
        )
    if unused_voice_asset_ids:
        add_vn_baseline_issue(
            issues,
            "soft",
            "voice_asset_unused",
            "部分语音素材还没有绑定台词",
            f"检测到 {len(unused_voice_asset_ids)} 条语音没有被台词/旁白引用：{', '.join(unused_voice_asset_names[:3])}",
            "把语音绑定到对应台词或先移出发布包；否则语音回听馆会缺内容，玩家也可能以为配音漏接。",
        )
    if configured_formal_save_slot_count != formal_save_slot_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "save_slot_count_clamped",
            "正式存档位配置超出安全范围",
            f"项目配置为 {raw_formal_save_slot_count} 个正式存档位，原生 Runtime 实际会使用 {formal_save_slot_count} 个。",
            f"把正式存档位调整到 {MIN_FORMAL_SAVE_SLOT_COUNT}-{MAX_FORMAL_SAVE_SLOT_COUNT} 之间，避免编辑器、导出包和玩家看到的槽位数量不一致。",
        )
    if scene_count >= 6 and formal_save_slot_count < 12:
        add_vn_baseline_issue(
            issues,
            "soft",
            "save_slot_count_low",
            "正式存档位可能偏少",
            f"当前 {scene_count} 个场景只配置了 {formal_save_slot_count} 个正式存档位。",
            "中长篇 Demo 建议至少保留 12-24 个正式存档位；如果作品有多路线或高密度选择，建议提高到 50 个以上。",
        )
    if scene_count >= 2 and ending_scene_count and credits_roll_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "credits_missing",
            "结局缺少片尾收束",
            f"检测到 {ending_scene_count} 个收束场景，但没有片尾字幕卡片。",
            "为正式版结局或试玩 Demo 补一个简短 STAFF / Thank You 片尾，能让作品结束感更完整。",
        )
    if dialogue_count >= 3 and character_show_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "character_stage",
            "人物登场演出偏弱",
            "台词数量已经成段，但没有检测到显示角色卡片。",
            "为主要角色补显示/隐藏、位置、缩放和淡入淡出，让原生试玩更像正式 VN。",
        )
    elif scene_count >= 2 and character_show_count and character_hide_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "character_hide_missing",
            "角色退场节奏未标记",
            "检测到角色登场，但没有隐藏角色卡片。",
            "章节切换或角色离场时补一个隐藏卡片，避免立绘残留。",
        )
    if character_show_count >= 3 and character_transition_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "character_transition_missing",
            "人物登场缺少基础转场",
            f"检测到 {character_show_count} 次角色登场，但没有淡入、滑入、上浮或弹出转场。",
            "给主要角色登场/退场设置轻量转场，不需要每张卡都动，但关键情绪点应避免硬切。",
        )
    character_stage_cue_count = character_show_count + character_move_count
    if character_stage_cue_count >= 3 and len(character_position_values) <= 1:
        add_vn_baseline_issue(
            issues,
            "soft",
            "character_position_static",
            "人物站位过于固定",
            f"检测到 {character_stage_cue_count} 次角色登场/动作，但只使用了 {len(character_position_values)} 种站位。",
            "为对话双方或重点角色使用 left / center / right，并用角色动作卡完成场内调度。",
        )
    if character_stage_cue_count >= 4 and character_stage_adjustment_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "character_stage_static",
            "人物舞台参数没有变化",
            "多次角色登场没有检测到缩放、透明度、偏移、翻转或层级调整。",
            "在近景、回忆、压迫感或角色切换时适当使用缩放/透明度/偏移，让立绘调度更接近正式 VN。",
        )
    if scene_count >= 2 and text_density < 2:
        add_vn_baseline_issue(
            issues,
            "soft",
            "text_density",
            "剧情密度偏低",
            f"平均每个场景只有 {text_density} 个台词/旁白/选项块。",
            "若不是纯演出 Demo，建议补足关键对白、旁白和过渡说明。",
        )
    if long_text_block_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "long_story_text",
            "部分文本卡片过长",
            f"检测到 {long_text_block_count} 张台词/旁白超过 {VN_TEXT_LONG_WARNING_LENGTH} 字：{', '.join(long_text_block_names[:3])}",
            "把长段落拆成多张台词或旁白卡，保留打字机节奏，也避免小屏幕文本框溢出。",
        )
    if multiline_text_block_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "multiline_story_text",
            "部分文本换行过多",
            f"检测到 {multiline_text_block_count} 张台词/旁白包含过多手动换行。",
            "手动换行过多会压缩可读区域；建议交给 Runtime 自动换行，或拆成更短的连续卡片。",
        )
    if dialog_box_readability_risk_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "dialog_box_readability_risk",
            "文本框可读性可能偏弱",
            "；".join(dialog_box_readability_notes[:4]) + "。",
            "提高文本框不透明度、扩大宽高和内边距，或使用对比更强的正文/底色组合；如果作品刻意透明，也建议跑一次浅色/复杂背景实机截图。",
        )
    if scene_count >= 3 and scenes_with_effects == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "presentation_polish",
            "缺少基础演出润色",
            "多场景项目没有检测到粒子、镜头或屏幕效果。",
            "为关键情绪点补轻量镜头、闪白、滤镜或粒子，不需要堆特效，但要有记忆点。",
        )

    warn_count = sum(1 for issue in issues if issue.get("severity") == "warn")
    soft_count = sum(1 for issue in issues if issue.get("severity") == "soft")
    status = "ready" if not issues else ("needs_fix" if warn_count else "needs_polish")
    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "status": status,
        "project": {
            "projectId": project.get("projectId"),
            "title": project.get("title") or project.get("name") or "未命名项目",
            "language": project.get("language") or DEFAULT_PROJECT_LANGUAGE,
        },
        "summary": {
            "statusLabel": {"ready": "基础完整", "needs_fix": "需要修复", "needs_polish": "建议润色"}.get(status, status),
            "warnCount": warn_count,
            "softCount": soft_count,
            "issueCount": len(issues),
            "recommendation": issues[0]["suggestion"] if issues else "基础视觉小说体验未发现明显缺口，可继续做目标系统实机点测。",
        },
        "metrics": {
            "chapterCount": len(chapters),
            "duplicateChapterIdCount": len(duplicate_chapter_ids),
            "emptyChapterCount": empty_chapter_count,
            "storySceneCount": scene_count,
            "missingSceneIdCount": missing_scene_id_count,
            "duplicateSceneIdCount": len(duplicate_scene_ids),
            "missingBlockIdCount": missing_block_id_count,
            "duplicateBlockIdCount": duplicate_block_id_count,
            "duplicateAssetIdCount": len(duplicate_asset_ids),
            "duplicateCharacterIdCount": len(duplicate_character_ids),
            "duplicateExpressionIdCount": duplicate_expression_id_count,
            "dialogueCount": dialogue_count,
            "narrationCount": narration_count,
            "choiceCount": choice_count,
            "variableCount": len(variables_by_id),
            "duplicateVariableIdCount": len(duplicate_variable_ids),
            "variableSetCount": variable_set_count,
            "variableAddCount": variable_add_count,
            "variableWrittenCount": len(variable_written_ids),
            "conditionReadVariableCount": len(condition_read_variable_ids),
            "routeInfluencingVariableCount": len(route_influencing_variable_ids),
            "unconsumedVariableWriteCount": len(unconsumed_variable_write_ids),
            "conditionCount": condition_count,
            "conditionBranchCount": condition_branch_count,
            "conditionRuleCount": condition_rule_count,
            "conditionEmptyBranchCount": condition_empty_branch_count,
            "missingNavigationTargetCount": missing_navigation_target_count,
            "implicitConditionFallbackEndCount": implicit_condition_fallback_end_count,
            "choiceEffectCount": choice_effect_count,
            "logicMissingVariableCount": logic_missing_variable_count,
            "logicNonNumberAddCount": logic_non_number_add_count,
            "logicOperatorMismatchCount": logic_operator_mismatch_count,
            "characterCount": len(characters),
            "charactersWithSpriteCount": characters_with_sprite,
            "characterShowCount": character_show_count,
            "characterMoveCount": character_move_count,
            "characterHideCount": character_hide_count,
            "characterTransitionCount": character_transition_count,
            "characterPositionVariantCount": len(character_position_values),
            "characterStageAdjustmentCount": character_stage_adjustment_count,
            "missingCharacterReferenceCount": missing_character_ref_count,
            "missingExpressionReferenceCount": missing_expression_ref_count,
            "scenesWithBackground": scenes_with_background,
            "backgroundBlockCount": background_block_count,
            "backgroundTransitionCount": background_transition_count,
            "backgroundAssetVariantCount": len(background_asset_ids),
            "missingBackgroundAssetCount": missing_background_asset_count,
            "cgAssetCount": len(cg_asset_ids),
            "cgUsedAssetCount": len(cg_used_asset_ids),
            "unusedCgAssetCount": len(unused_cg_asset_ids),
            "scenesWithMusic": scenes_with_music,
            "scenesWithEffects": scenes_with_effects,
            "choiceOptionCount": choice_option_count,
            "emptyChoiceOptionCount": empty_choice_option_count,
            "longChoiceOptionCount": long_choice_option_count,
            "duplicateChoiceOptionCount": duplicate_choice_option_count,
            "crowdedChoiceBlockCount": crowded_choice_block_count,
            "noActionChoiceOptionCount": no_action_choice_option_count,
            "sameTargetChoiceCount": same_target_choice_count,
            "sameTargetConditionCount": same_target_condition_count,
            "sfxPlayCount": sfx_play_count,
            "missingSfxAssetCount": missing_sfx_asset_count,
            "videoAssetCount": video_asset_count,
            "videoPlayCount": video_play_count,
            "missingVideoAssetCount": missing_video_asset_count,
            "endingSceneCount": ending_scene_count,
            "creditsRollCount": credits_roll_count,
            "creditsLineCount": credits_line_count,
            "emptyCreditsRollCount": empty_credits_roll_count,
            "shortCreditsRollCount": short_credits_roll_count,
            "musicPlayCount": music_play_count,
            "musicStopCount": music_stop_count,
            "musicScopedCount": music_scoped_count,
            "musicAfterBlockScopeCount": music_after_block_scope_count,
            "missingMusicEndBlockCount": missing_music_end_block_count,
            "backwardMusicEndBlockCount": backward_music_end_block_count,
            "musicFadeInCount": music_fade_in_count,
            "musicFadeOutCount": music_fade_out_count,
            "bgmAssetCount": len(bgm_asset_ids),
            "bgmUsedAssetCount": len(music_used_asset_ids & bgm_asset_ids),
            "unusedBgmAssetCount": len(unused_bgm_asset_ids),
            "missingMusicAssetCount": missing_music_asset_count,
            "voiceEligibleLineCount": voice_eligible_line_count,
            "voiceBoundLineCount": voice_bound_line_count,
            "dialogueVoiceCount": dialogue_voice_count,
            "narrationVoiceCount": narration_voice_count,
            "voiceCoveragePercent": voice_coverage_percent,
            "missingVoiceAssetCount": missing_voice_asset_count,
            "voiceAssetCount": len(voice_asset_ids),
            "voiceUsedAssetCount": len(voice_used_asset_ids & voice_asset_ids),
            "unusedVoiceAssetCount": len(unused_voice_asset_ids),
            "sfxAssetCount": len(sfx_asset_ids),
            "sfxUsedAssetCount": len(sfx_used_asset_ids & sfx_asset_ids),
            "unusedSfxAssetCount": len(unused_sfx_asset_ids),
            "supportedLanguageCount": len(supported_languages),
            "targetI18nLanguageCount": len(target_i18n_languages),
            "i18nTranslatableEntryCount": i18n_translatable_entry_count,
            "i18nExpectedTranslationCount": i18n_expected_translation_count,
            "i18nPresentTranslationCount": i18n_present_translation_count,
            "i18nTranslationCoveragePercent": i18n_translation_coverage_percent,
            "i18nFallbackSupported": fallback_language in supported_languages,
            "fontAssetCount": font_asset_count,
            "fontFamilyConfigured": font_status["fontFamilyConfigured"],
            "customFontAssetBound": font_status["customFontAssetBound"],
            "fontAssetUsable": font_status["fontAssetUsable"],
            "fontAssetMissingCount": font_status["fontAssetMissingCount"],
            "fontAssetTypeRiskCount": font_status["fontAssetTypeRiskCount"],
            "fontExtensionRiskCount": font_status["fontExtensionRiskCount"],
            "formalSaveSlotCount": formal_save_slot_count,
            "configuredFormalSaveSlotCount": configured_formal_save_slot_count,
            "saveDialogPageCount": save_dialog_page_count,
            "saveSlotCountClamped": configured_formal_save_slot_count != formal_save_slot_count,
            "entrySceneExists": entry_scene_id in valid_scene_ids,
            "routeTargetMissingCount": len(missing_route_targets),
            "unreachableSceneCount": len(unreachable_scene_ids),
            "linkedSceneCount": len(reachable_scene_ids),
            "reachableTerminalSceneCount": reachable_terminal_scene_count,
            "reachableCreditsTerminalSceneCount": reachable_credits_terminal_scene_count,
            "reachablePlainTerminalSceneCount": len(reachable_plain_terminal_scene_names),
            "placeholderAssetCount": len(placeholder_assets),
            "emptyTextBlockCount": empty_text_count,
            "longTextBlockCount": long_text_block_count,
            "multilineTextBlockCount": multiline_text_block_count,
            "dialogBoxReadabilityRiskCount": dialog_box_readability_risk_count,
            "dialogBoxBackgroundOpacity": dialog_box_background_opacity,
            "dialogBoxPanelAssetOpacity": dialog_box_panel_asset_opacity,
            "dialogBoxHasPanelArt": dialog_box_has_panel_art,
            "dialogBoxTextContrastRatio": dialog_box_text_contrast_ratio,
            "dialogBoxWidthPercent": int(dialog_box_config.get("widthPercent") or 0),
            "dialogBoxMinHeight": int(dialog_box_config.get("minHeight") or 0),
            "dialogBoxPaddingX": int(dialog_box_config.get("paddingX") or 0),
            "dialogBoxPaddingY": int(dialog_box_config.get("paddingY") or 0),
            "textDensity": text_density,
            "averageTextLength": average_text_length,
        },
        "issues": issues,
    }
