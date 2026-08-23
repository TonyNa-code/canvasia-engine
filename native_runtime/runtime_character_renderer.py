from __future__ import annotations

try:
    from .runtime_character_motion import (
        build_native_renderable_character_items,
        get_native_character_transition_adjustment,
    )
    from .runtime_player_view import clamp, get_safe_character_stage, with_alpha
    from .runtime_speaker_focus import scale_rgb_color
    from .runtime_surface_cache import get_cached_transformed_surface, get_runtime_surface_cache
    from .runtime_voice_reactive_motion import NativeVoiceReactiveMotionController
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_character_motion import (
        build_native_renderable_character_items,
        get_native_character_transition_adjustment,
    )
    from runtime_player_view import clamp, get_safe_character_stage, with_alpha
    from runtime_speaker_focus import scale_rgb_color
    from runtime_surface_cache import get_cached_transformed_surface, get_runtime_surface_cache
    from runtime_voice_reactive_motion import NativeVoiceReactiveMotionController


def render_native_characters(runtime, target=None) -> None:
    """Draw character sprites while keeping the main Runtime controller focused on playback."""
    target = target or runtime.screen
    palette = runtime.get_active_palette()
    now_ms = runtime.get_runtime_ticks_ms()
    visual_comfort_mode = str(runtime.runtime_settings.get("visualComfort") or "standard")
    active_character_id = str((runtime.current_line or {}).get("speakerId") or "").strip()
    voice_active = runtime.is_voice_playing()
    voice_motion_controller = getattr(runtime, "voice_reactive_motion_controller", None)
    if voice_motion_controller is None:
        voice_motion_controller = NativeVoiceReactiveMotionController()
        runtime.voice_reactive_motion_controller = voice_motion_controller
    position_x = {
        "left": int(runtime.width * 0.24),
        "center": int(runtime.width * 0.50),
        "right": int(runtime.width * 0.76),
    }
    character_items = build_native_renderable_character_items(
        runtime.visible_characters,
        runtime.leaving_characters,
        runtime.character_motions,
        now_ms,
    )
    speaker_focus_poses = runtime.speaker_focus_controller.build_render_poses(
        items=character_items,
        current_line=runtime.current_line,
        game_ui_config=runtime.game_ui_config,
        visual_comfort_mode=visual_comfort_mode,
        now_ms=now_ms,
    )

    def character_sort_key(item):
        character_state = item[1] if isinstance(item[1], dict) else {}
        stage = get_safe_character_stage(character_state.get("stage"))
        focus_pose = runtime.speaker_focus_controller.get_render_pose(speaker_focus_poses, item[0], character_state)
        return (
            stage["layer"],
            int(focus_pose.get("layerBoost") or 0),
            float(character_state.get("positionRatio") or 0),
        )

    for character_id, state in sorted(character_items, key=character_sort_key):
        stage = get_safe_character_stage(state.get("stage"))
        is_leaving = bool(state.get("__leaving"))
        focus_pose = runtime.speaker_focus_controller.get_render_pose(speaker_focus_poses, character_id, state)
        voice_pose = voice_motion_controller.build_render_pose(
            character_id=character_id,
            active_character_id=active_character_id,
            voice_active=voice_active,
            game_ui_config=runtime.game_ui_config,
            visual_comfort_mode=visual_comfort_mode,
            now_ms=now_ms,
            is_leaving=is_leaving,
        )
        sprite_asset_id = runtime.get_character_sprite_asset_id(character_id, state.get("expressionId"))
        sprite = runtime._load_image(sprite_asset_id)
        position_ratio = state.get("positionRatio")
        x = (
            int(runtime.width * float(position_ratio))
            if isinstance(position_ratio, (int, float))
            else position_x.get(state.get("position") or "center", runtime.width // 2)
        ) + int(runtime.width * stage["offsetX"] / 100)
        bottom_y = (
            int(runtime.height * 0.88)
            + int(runtime.height * stage["offsetY"] / 100)
            + int(runtime.height * float(voice_pose["offsetYPercent"]) / 100)
        )
        if sprite:
            sprite_width, sprite_height = sprite.get_size()
            max_height = int(runtime.height * 0.74)
            scale = min(max_height / max(sprite_height, 1), 1.6) * (stage["scale"] / 100)
            transition_adjustment = get_native_character_transition_adjustment(
                state,
                max(1, int(sprite_width * scale)),
                max(1, int(sprite_height * scale)),
                is_leaving,
                now_ms,
            )
            scale *= (
                transition_adjustment["scaleMultiplier"]
                * float(focus_pose["scaleMultiplier"])
                * float(voice_pose["scaleMultiplier"])
            )
            scaled = get_cached_transformed_surface(
                get_runtime_surface_cache(runtime),
                runtime.pygame,
                sprite,
                (max(1, int(sprite_width * scale)), max(1, int(sprite_height * scale))),
                namespace="character-sprite",
                flip_x=stage["flipX"],
            )
            brightness_multiplier = float(focus_pose["brightnessMultiplier"])
            effective_opacity = clamp(
                stage["opacity"]
                * transition_adjustment["opacityMultiplier"]
                * float(focus_pose["opacityMultiplier"]),
                0,
                100,
            )
            if brightness_multiplier < 0.999 or effective_opacity < 100:
                scaled = scaled.copy()
            if brightness_multiplier < 0.999:
                shade = max(0, min(255, round(255 * brightness_multiplier)))
                scaled.fill((shade, shade, shade, 255), special_flags=runtime.pygame.BLEND_RGBA_MULT)
            if effective_opacity < 100:
                scaled.set_alpha(int(255 * effective_opacity / 100))
            rect = scaled.get_rect(
                midbottom=(
                    x + int(transition_adjustment["offsetX"]),
                    bottom_y + int(transition_adjustment["offsetY"]),
                )
            )
            target.blit(scaled, rect)
            character = runtime.characters_by_id.get(character_id) or {}
            if effective_opacity > 15 and not is_leaving:
                runtime.render_character_model_preview_card(target, rect, character, state.get("expressionId"))
            continue

        transition_adjustment = get_native_character_transition_adjustment(
            state,
            220,
            420,
            is_leaving,
            now_ms,
        )
        placeholder_rect = runtime.pygame.Rect(0, 0, 220, 420)
        placeholder_scale = (
            stage["scale"]
            / 100
            * transition_adjustment["scaleMultiplier"]
            * float(focus_pose["scaleMultiplier"])
            * float(voice_pose["scaleMultiplier"])
        )
        placeholder_rect.width = max(1, int(placeholder_rect.width * placeholder_scale))
        placeholder_rect.height = max(1, int(placeholder_rect.height * placeholder_scale))
        placeholder_rect.midbottom = (
            x + int(transition_adjustment["offsetX"]),
            bottom_y + int(transition_adjustment["offsetY"]),
        )
        effective_opacity = clamp(
            stage["opacity"]
            * transition_adjustment["opacityMultiplier"]
            * float(focus_pose["opacityMultiplier"]),
            0,
            100,
        )
        brightness_multiplier = float(focus_pose["brightnessMultiplier"])
        placeholder_surface = runtime.pygame.Surface(placeholder_rect.size, runtime.pygame.SRCALPHA)
        runtime.pygame.draw.rect(
            placeholder_surface,
            with_alpha(scale_rgb_color(palette["placeholder"], brightness_multiplier), effective_opacity),
            placeholder_surface.get_rect(),
            border_radius=28,
        )
        runtime.pygame.draw.rect(
            placeholder_surface,
            with_alpha(
                palette["accent"] if focus_pose.get("active") else scale_rgb_color(palette["panelBorder"], brightness_multiplier),
                effective_opacity,
            ),
            placeholder_surface.get_rect(),
            2,
            border_radius=28,
        )
        target.blit(placeholder_surface, placeholder_rect)
        character = runtime.characters_by_id.get(character_id) or {}
        character_name = runtime.localize_value(character, "displayName", character_id)
        presentation_label = runtime.get_character_presentation_mode_label(character)
        model_asset_label = runtime.get_character_model_asset_label(character)
        binding_label = runtime.get_character_expression_binding_label(character, state.get("expressionId"))
        if effective_opacity > 15:
            runtime.blit_text_center(runtime.font_body, character_name, placeholder_rect.centerx, placeholder_rect.centery - 16, scale_rgb_color(palette["text"], brightness_multiplier), target=target)
            runtime.blit_text_center(runtime.font_ui, presentation_label, placeholder_rect.centerx, placeholder_rect.centery + 22, scale_rgb_color(palette["accent"], brightness_multiplier), target=target)
            runtime.blit_text_center(runtime.font_ui, model_asset_label, placeholder_rect.centerx, placeholder_rect.centery + 52, scale_rgb_color(palette["muted"], brightness_multiplier), target=target)
            runtime.blit_text_center(runtime.font_ui, binding_label[:32], placeholder_rect.centerx, placeholder_rect.centery + 80, scale_rgb_color(palette["muted"], brightness_multiplier), target=target)
        if not is_leaving:
            runtime.render_character_model_preview_card(target, placeholder_rect, character, state.get("expressionId"))
