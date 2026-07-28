from __future__ import annotations

import math

try:
    from .runtime_player_view import (
        clamp_int,
        ease_out_cubic,
        ellipsize_text,
        get_native_transition_progress,
        get_safe_screen_color_grade,
        with_alpha,
    )
    from .runtime_stage_images import build_native_renderable_stage_image_items, get_safe_stage_image_transform
    from .runtime_visual_comfort import scale_visual_motion
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_player_view import (
        clamp_int,
        ease_out_cubic,
        ellipsize_text,
        get_native_transition_progress,
        get_safe_screen_color_grade,
        with_alpha,
    )
    from runtime_stage_images import build_native_renderable_stage_image_items, get_safe_stage_image_transform
    from runtime_visual_comfort import scale_visual_motion


SHAKE_DISTANCE = {"light": 4, "medium": 9, "heavy": 16}
SCREEN_FILTER_WASH = {
    "memory": ((255, 207, 150), 38),
    "mono": ((180, 190, 205), 42),
    "dream": ((172, 145, 255), 44),
    "cold": ((122, 184, 255), 42),
}
SCREEN_FILTER_STRENGTH_MULTIPLIER = {"soft": 0.62, "medium": 1.0, "strong": 1.38}
DEPTH_BLUR_ALPHA = {"soft": 24, "medium": 42, "strong": 64}


def _mix_rgb(color_a: tuple[int, int, int], color_b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    ratio = max(0.0, min(1.0, float(amount or 0)))
    return tuple(round(a + (b - a) * ratio) for a, b in zip(color_a[:3], color_b[:3]))


def get_native_stage_shake_offset(runtime) -> tuple[int, int]:
    if not runtime.screen_shake_effect:
        return (0, 0)
    intensity = str(runtime.screen_shake_effect.get("intensity") or "medium")
    distance = scale_visual_motion(
        SHAKE_DISTANCE.get(intensity, SHAKE_DISTANCE["medium"]),
        runtime.runtime_settings.get("visualComfort"),
    )
    phase = runtime.runtime_elapsed_seconds * 74.0
    return (int(math.sin(phase) * distance), int(math.cos(phase * 1.31) * distance * 0.55))


def render_native_stage_surface(runtime, stage_surface) -> None:
    camera_pose = runtime.dialogue_camera_controller.build_render_pose(
        camera_zoom=runtime.camera_zoom_effect,
        camera_pan=runtime.camera_pan_effect,
        current_line=runtime.current_line,
        visible_characters=runtime.visible_characters,
        game_ui_config=runtime.game_ui_config,
        visual_comfort_mode=str(runtime.runtime_settings.get("visualComfort") or "standard"),
        now_ms=runtime.get_runtime_ticks_ms(),
    )
    scale = float(camera_pose.get("zoomScale") or 1.0)
    offset_x = int(round(runtime.width * float(camera_pose.get("panPercent") or 0) / 100))
    focus_ratio = float(camera_pose.get("focusPercent") or 50) / 100
    zoom_anchor_offset_x = int(round(runtime.width * (focus_ratio - 0.5) * (1 - scale)))
    shake_x, shake_y = get_native_stage_shake_offset(runtime)
    if abs(scale - 1.0) > 0.01:
        scaled_size = (max(1, int(runtime.width * scale)), max(1, int(runtime.height * scale)))
        stage_surface = runtime.pygame.transform.smoothscale(stage_surface, scaled_size)
    rect = stage_surface.get_rect(
        center=(
            runtime.width // 2 + offset_x + zoom_anchor_offset_x + shake_x,
            runtime.height // 2 + shake_y,
        )
    )
    runtime.screen.blit(stage_surface, rect)


def render_native_stage_effect_overlays(runtime) -> None:
    if runtime.screen_filter_effect:
        preset = str(runtime.screen_filter_effect.get("preset") or "memory")
        strength = str(runtime.screen_filter_effect.get("strength") or "medium")
        grade = get_safe_screen_color_grade(runtime.screen_filter_effect.get("grade"))
        wash_color, base_alpha = SCREEN_FILTER_WASH.get(preset, SCREEN_FILTER_WASH["memory"])
        alpha = int(base_alpha * SCREEN_FILTER_STRENGTH_MULTIPLIER.get(strength, 1.0))
        wash = runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
        wash.fill((*wash_color, max(0, min(160, alpha))))
        runtime.screen.blit(wash, (0, 0))

        temperature = int(grade.get("temperature") or 0)
        if temperature:
            temp_color = (255, 184, 102) if temperature > 0 else (108, 172, 255)
            temp_alpha = int(min(54, abs(temperature) / 100 * 54))
            temp_wash = runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
            temp_wash.fill((*temp_color, temp_alpha))
            runtime.screen.blit(temp_wash, (0, 0))

        brightness_delta = int(grade.get("brightness") or 100) - 100
        if brightness_delta:
            tone = 255 if brightness_delta > 0 else 0
            tone_alpha = int(min(72, abs(brightness_delta) / 80 * 72))
            tone_wash = runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
            tone_wash.fill((tone, tone, tone, tone_alpha))
            runtime.screen.blit(tone_wash, (0, 0))

        contrast_delta = int(grade.get("contrast") or 100) - 100
        if contrast_delta > 0:
            multiplier = 255 - int(min(42, contrast_delta / 80 * 42))
            contrast_wash = runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
            contrast_wash.fill((multiplier, multiplier, multiplier, 255))
            runtime.screen.blit(contrast_wash, (0, 0), special_flags=runtime.pygame.BLEND_RGBA_MULT)
        elif contrast_delta < 0:
            flat_alpha = int(min(42, abs(contrast_delta) / 80 * 42))
            flat_wash = runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
            flat_wash.fill((140, 148, 160, flat_alpha))
            runtime.screen.blit(flat_wash, (0, 0))

        saturation_delta = int(grade.get("saturation") or 100) - 100
        if saturation_delta < 0:
            gray_alpha = int(min(58, abs(saturation_delta) / 100 * 58))
            gray_wash = runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
            gray_wash.fill((184, 192, 206, gray_alpha))
            runtime.screen.blit(gray_wash, (0, 0))

        hue_shift = int(grade.get("hue") or 0)
        if hue_shift:
            hue_color = (142, 106, 255) if hue_shift > 0 else (94, 222, 184)
            hue_alpha = int(min(34, abs(hue_shift) / 180 * 34))
            hue_wash = runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
            hue_wash.fill((*hue_color, hue_alpha))
            runtime.screen.blit(hue_wash, (0, 0))

        vignette = int(grade.get("vignette") or 0)
        if vignette > 0:
            vignette_surface = runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
            max_alpha = int(min(122, vignette / 100 * 122))
            band = max(1, int(min(runtime.width, runtime.height) * 0.16))
            for index in range(6):
                ratio = (index + 1) / 6
                alpha_step = int(max_alpha * ratio)
                inset = int(band * (1 - ratio))
                edge = max(1, band - inset)
                runtime.pygame.draw.rect(vignette_surface, (2, 6, 12, alpha_step), runtime.pygame.Rect(0, 0, runtime.width, edge))
                runtime.pygame.draw.rect(vignette_surface, (2, 6, 12, alpha_step), runtime.pygame.Rect(0, runtime.height - edge, runtime.width, edge))
                runtime.pygame.draw.rect(vignette_surface, (2, 6, 12, alpha_step), runtime.pygame.Rect(0, 0, edge, runtime.height))
                runtime.pygame.draw.rect(vignette_surface, (2, 6, 12, alpha_step), runtime.pygame.Rect(runtime.width - edge, 0, edge, runtime.height))
            runtime.screen.blit(vignette_surface, (0, 0))

    if runtime.depth_blur_effect:
        strength = str(runtime.depth_blur_effect.get("strength") or "medium")
        focus = str(runtime.depth_blur_effect.get("focus") or "full")
        alpha = DEPTH_BLUR_ALPHA.get(strength, DEPTH_BLUR_ALPHA["medium"])
        shade = runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
        shade.fill((0, 0, 0, 0 if focus in {"left", "right", "center"} else alpha))
        if focus == "left":
            runtime.pygame.draw.rect(shade, (0, 0, 0, alpha), runtime.pygame.Rect(int(runtime.width * 0.42), 0, int(runtime.width * 0.58), runtime.height))
        elif focus == "right":
            runtime.pygame.draw.rect(shade, (0, 0, 0, alpha), runtime.pygame.Rect(0, 0, int(runtime.width * 0.58), runtime.height))
        elif focus == "center":
            runtime.pygame.draw.rect(shade, (0, 0, 0, alpha), runtime.pygame.Rect(0, 0, int(runtime.width * 0.26), runtime.height))
            runtime.pygame.draw.rect(shade, (0, 0, 0, alpha), runtime.pygame.Rect(int(runtime.width * 0.74), 0, int(runtime.width * 0.26), runtime.height))
        runtime.screen.blit(shade, (0, 0))


def project_native_scene3d_grid_point(runtime, x: float, z: float, center_x: int, center_y: int, scale: float) -> tuple[int, int]:
    yaw = math.radians(float(runtime.scene3d_preview_yaw))
    pitch_ratio = math.sin(math.radians(float(runtime.scene3d_preview_pitch)))
    rotated_x = x * math.cos(yaw) - z * math.sin(yaw)
    rotated_z = x * math.sin(yaw) + z * math.cos(yaw)
    screen_x = center_x + rotated_x * scale
    screen_y = center_y + rotated_z * scale * (0.20 + 0.48 * pitch_ratio)
    return int(round(screen_x)), int(round(screen_y))


def render_native_scene3d_background_preview(runtime, target, asset: dict) -> None:
    palette = runtime.get_active_palette()
    target.fill(_mix_rgb(palette["bgTop"], (0, 0, 0), 0.16))
    glow = runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
    for index, radius in enumerate([520, 360, 220]):
        alpha = max(18, 58 - index * 16)
        runtime.pygame.draw.circle(glow, (*palette["accent"], alpha), (runtime.width // 2, int(runtime.height * 0.38)), radius)
    target.blit(glow, (0, 0))

    center_x = runtime.width // 2
    center_y = int(runtime.height * 0.58)
    scale = 42 * float(runtime.scene3d_preview_zoom)
    line_color = with_alpha(palette["accent"], 34)
    axis_color = with_alpha(palette["accentAlt"], 70)
    for value in range(-9, 10):
        start = project_native_scene3d_grid_point(runtime, value, -9, center_x, center_y, scale)
        end = project_native_scene3d_grid_point(runtime, value, 9, center_x, center_y, scale)
        runtime.pygame.draw.line(target, axis_color if value == 0 else line_color, start, end, 2 if value == 0 else 1)
        start = project_native_scene3d_grid_point(runtime, -9, value, center_x, center_y, scale)
        end = project_native_scene3d_grid_point(runtime, 9, value, center_x, center_y, scale)
        runtime.pygame.draw.line(target, axis_color if value == 0 else line_color, start, end, 2 if value == 0 else 1)

    asset_id = str(asset.get("id") or "")
    report = runtime.get_scene3d_preview_report(asset_id)
    panel_rect = runtime.pygame.Rect(0, 0, min(520, runtime.width - 96), 178)
    panel_rect.center = (runtime.width // 2, int(runtime.height * 0.28))
    runtime.pygame.draw.rect(target, (*palette["panel"], 224), panel_rect, border_radius=24)
    runtime.pygame.draw.rect(target, with_alpha(palette["accent"], 62), panel_rect, 2, border_radius=24)
    target.blit(runtime.font_title.render("3D 场景交互预览桥", True, palette["text"]), (panel_rect.left + 24, panel_rect.top + 18))
    status_color = palette["accent"] if report.get("status") == "ready" else palette["warning"]
    status_surface = runtime.font_ui.render(str(report.get("statusLabel") or "待检查"), True, status_color)
    target.blit(status_surface, (panel_rect.right - status_surface.get_width() - 24, panel_rect.top + 26))
    y = panel_rect.top + 66
    for line in runtime.get_scene3d_preview_lines(asset_id)[1:]:
        clipped = ellipsize_text(runtime.font_ui, line, panel_rect.width - 48)
        target.blit(runtime.font_ui.render(clipped, True, palette["muted"]), (panel_rect.left + 24, y))
        y += 24


def render_native_background_asset(runtime, target, asset_id: str | None, alpha: int = 255) -> None:
    target = target or runtime.screen
    palette = runtime.get_active_palette()
    safe_asset_id = str(asset_id or "").strip()
    safe_alpha = clamp_int(alpha, 0, 255, 255)
    render_target = target if safe_alpha >= 255 else runtime.pygame.Surface((runtime.width, runtime.height), runtime.pygame.SRCALPHA)
    background_asset = runtime.assets_by_id.get(safe_asset_id) or {}
    if background_asset.get("type") == "scene3d":
        render_native_scene3d_background_preview(runtime, render_target, background_asset)
        if safe_alpha < 255:
            render_target.set_alpha(safe_alpha)
            target.blit(render_target, (0, 0))
        return
    background = runtime._load_image(safe_asset_id)
    if background:
        bg_width, bg_height = background.get_size()
        scale = max(runtime.width / bg_width, runtime.height / bg_height)
        scaled = runtime.pygame.transform.smoothscale(background, (max(1, int(bg_width * scale)), max(1, int(bg_height * scale))))
        render_target.blit(scaled, scaled.get_rect(center=(runtime.width // 2, runtime.height // 2)))
    else:
        top = runtime.pygame.Surface((runtime.width, runtime.height // 2))
        bottom = runtime.pygame.Surface((runtime.width, runtime.height - runtime.height // 2))
        top.fill(palette["bgTop"])
        bottom.fill(palette["bgBottom"])
        render_target.blit(top, (0, 0))
        render_target.blit(bottom, (0, runtime.height // 2))
        label = "背景未加载" if safe_asset_id else "当前场景没有背景"
        runtime.blit_text_center(runtime.font_title, label, runtime.width // 2, runtime.height // 2 - 20, palette["muted"], target=render_target)
    if safe_alpha < 255:
        render_target.set_alpha(safe_alpha)
        target.blit(render_target, (0, 0))


def render_native_background(runtime, target=None) -> None:
    target = target or runtime.screen
    render_native_background_asset(runtime, target, runtime.stage_background_asset_id)
    transition = runtime.background_transition
    if not transition:
        return
    progress = get_native_transition_progress(transition, runtime.get_runtime_ticks_ms())
    if progress >= 1.0:
        runtime.background_transition = None
        return
    previous_alpha = int(round(255 * (1.0 - ease_out_cubic(progress))))
    if previous_alpha > 0:
        render_native_background_asset(runtime, target, transition.get("previousAssetId"), previous_alpha)


def render_native_character_model_preview_card(runtime, target, anchor_rect, character: dict, expression_id: str | None) -> None:
    report = runtime.get_character_model_preview_report(character, expression_id)
    if not report.get("isAdvanced"):
        return
    palette = runtime.get_active_palette()
    status = str(report.get("status") or "")
    accent = palette["accent"] if status == "ready" else palette["warning"]
    if status in {"missing_asset", "missing_file", "invalid", "unbound"}:
        accent = _mix_rgb(palette["warning"], (255, 64, 64), 0.34)
    card_width = min(300, max(238, int(runtime.width * 0.22)))
    card_height = 128
    card_x = max(18, min(runtime.width - card_width - 18, int(anchor_rect.centerx - card_width / 2)))
    card_y = anchor_rect.top - card_height - 14 if anchor_rect.top > 156 else anchor_rect.bottom - card_height - 18
    card_y = max(92, min(runtime.height - card_height - 150, card_y))
    card_rect = runtime.pygame.Rect(card_x, card_y, card_width, card_height)
    runtime.pygame.draw.rect(target, (*palette["panel"], 226), card_rect, border_radius=18)
    runtime.pygame.draw.rect(target, with_alpha(accent, 68), card_rect, 2, border_radius=18)
    runtime.pygame.draw.line(target, (*accent, 190), (card_rect.left + 18, card_rect.top + 34), (card_rect.right - 18, card_rect.top + 34), 2)
    title = f"{report['modeLabel']} 预览桥"
    target.blit(runtime.font_ui.render(title, True, palette["text"]), (card_rect.left + 16, card_rect.top + 10))
    status_surface = runtime.font_ui.render(str(report.get("statusLabel") or "待检查"), True, accent)
    target.blit(status_surface, (card_rect.right - status_surface.get_width() - 16, card_rect.top + 10))
    y = card_rect.top + 44
    for line in runtime.get_character_model_preview_lines(character, expression_id)[1:5]:
        clipped = ellipsize_text(runtime.font_ui, line, card_rect.width - 30)
        target.blit(runtime.font_ui.render(clipped, True, palette["muted"]), (card_rect.left + 16, y))
        y += 20


def render_native_stage_images(runtime, target, plane: str) -> None:
    palette = runtime.get_active_palette()
    renderable_items = build_native_renderable_stage_image_items(
        runtime.visible_stage_images,
        runtime.leaving_stage_images,
        runtime.stage_image_motions,
        plane,
        runtime.get_runtime_ticks_ms(),
    )
    for layer_id, state in renderable_items:
        transform = get_safe_stage_image_transform(state.get("transform"))
        image = runtime._load_image(state.get("assetId"))
        position_ratio = float(state.get("positionRatio") or 0.5)
        center_x = int(runtime.width * position_ratio + runtime.width * transform["offsetX"] / 100)
        center_y = int(runtime.height * 0.5 + runtime.height * transform["offsetY"] / 100)
        target_width = max(1, int(runtime.width * transform["width"] / 100))
        if image:
            source_width, source_height = image.get_size()
            target_height = max(1, int(source_height * target_width / max(source_width, 1)))
            scaled = runtime.pygame.transform.smoothscale(image, (target_width, target_height))
            if transform["flipX"]:
                scaled = runtime.pygame.transform.flip(scaled, True, False)
            if transform["rotation"]:
                scaled = runtime.pygame.transform.rotate(scaled, -float(transform["rotation"]))
            if transform["opacity"] < 100:
                scaled = scaled.copy()
                scaled.set_alpha(int(255 * transform["opacity"] / 100))
            target.blit(scaled, scaled.get_rect(center=(center_x, center_y)))
            continue
        placeholder_width = min(target_width, max(120, int(runtime.width * 0.34)))
        placeholder_height = max(72, int(placeholder_width * 0.38))
        placeholder = runtime.pygame.Surface((placeholder_width, placeholder_height), runtime.pygame.SRCALPHA)
        alpha = int(180 * transform["opacity"] / 100)
        runtime.pygame.draw.rect(placeholder, (*palette["panel"], alpha), placeholder.get_rect(), border_radius=18)
        runtime.pygame.draw.rect(placeholder, (*palette["panelBorder"], alpha), placeholder.get_rect(), 2, border_radius=18)
        label = ellipsize_text(runtime.font_ui, str(layer_id or "舞台贴图"), placeholder_width - 24)
        label_surface = runtime.font_ui.render(label, True, palette["muted"])
        placeholder.blit(label_surface, label_surface.get_rect(center=placeholder.get_rect().center))
        target.blit(placeholder, placeholder.get_rect(center=(center_x, center_y)))
