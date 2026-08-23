from __future__ import annotations

try:
    from .runtime_player_view import COLOR_PANEL, COLOR_PANEL_BORDER, with_alpha
    from .runtime_surface_cache import get_cached_transformed_surface, get_runtime_surface_cache
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_player_view import COLOR_PANEL, COLOR_PANEL_BORDER, with_alpha
    from runtime_surface_cache import get_cached_transformed_surface, get_runtime_surface_cache


DIALOG_PANEL_CACHE_VERSION = 1


def _cache_value(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return tuple(_cache_value(item) for item in value)
    if isinstance(value, dict):
        return tuple(sorted((str(key), _cache_value(item)) for key, item in value.items()))
    try:
        hash(value)
    except TypeError:
        return repr(value)
    return value


def build_dialog_panel_render_plan(runtime, rect) -> dict:
    config = runtime.dialog_box_config if isinstance(runtime.dialog_box_config, dict) else {}
    radius = int(runtime.get_dialog_border_radius(rect.height))
    shadow_strength = max(0, int(config.get("shadowStrength", 0)))
    shadow_alpha = min(190, int(70 + shadow_strength * 2.2)) if shadow_strength else 0
    background_opacity = runtime.scale_dialog_opacity(int(config.get("backgroundOpacity", 0)))
    panel_art_id = str(config.get("panelAssetId") or "").strip()
    panel_art_opacity = runtime.scale_dialog_opacity(int(config.get("panelAssetOpacity", 0)))
    panel_art = runtime._load_image(panel_art_id) if panel_art_id and panel_art_opacity > 0 else None
    panel_art_size = panel_art.get_size() if panel_art else (0, 0)
    panel_art_fit = "contain" if config.get("panelAssetFit") == "contain" else "cover"
    border_width = max(0, int(config.get("borderWidth", 0)))
    border_opacity = max(0, int(config.get("borderOpacity", 0)))
    has_shadow = shadow_alpha > 0
    surface_position = (rect.left - 16, rect.top - 8) if has_shadow else rect.topleft
    surface_size = (rect.width + 32, rect.height + 32) if has_shadow else rect.size
    panel_origin = (16, 8) if has_shadow else (0, 0)

    cache_key = (
        "dialog-panel-chrome",
        DIALOG_PANEL_CACHE_VERSION,
        rect.width,
        rect.height,
        radius,
        shadow_strength,
        shadow_alpha,
        background_opacity,
        _cache_value(config.get("backgroundColor", COLOR_PANEL)),
        panel_art_id,
        id(panel_art) if panel_art else 0,
        panel_art_size,
        panel_art_fit,
        panel_art_opacity,
        border_width,
        border_opacity,
        _cache_value(config.get("borderColor", COLOR_PANEL_BORDER)),
    )
    return {
        "cacheKey": cache_key,
        "surfacePosition": surface_position,
        "surfaceSize": surface_size,
        "panelOrigin": panel_origin,
        "panelSize": rect.size,
        "radius": radius,
        "shadowAlpha": shadow_alpha,
        "backgroundOpacity": background_opacity,
        "backgroundColor": config.get("backgroundColor", COLOR_PANEL),
        "panelArt": panel_art,
        "panelArtFit": panel_art_fit,
        "panelArtOpacity": panel_art_opacity,
        "borderWidth": border_width,
        "borderOpacity": border_opacity,
        "borderColor": config.get("borderColor", COLOR_PANEL_BORDER),
    }


def build_dialog_panel_surface(runtime, plan: dict):
    pygame = runtime.pygame
    composed = pygame.Surface(plan["surfaceSize"], pygame.SRCALPHA)
    panel_width, panel_height = plan["panelSize"]
    panel_origin = plan["panelOrigin"]
    radius = int(plan["radius"])

    if plan["shadowAlpha"] > 0:
        pygame.draw.rect(
            composed,
            (0, 0, 0, int(plan["shadowAlpha"])),
            pygame.Rect(16, 16, panel_width, panel_height),
            border_radius=min(radius + 6, (panel_height + 12) // 2),
        )

    panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_rect = panel_surface.get_rect()
    if plan["backgroundOpacity"] > 0:
        pygame.draw.rect(
            panel_surface,
            with_alpha(plan["backgroundColor"], int(plan["backgroundOpacity"])),
            panel_rect,
            border_radius=radius,
        )

    panel_art = plan.get("panelArt")
    if panel_art:
        art_width, art_height = panel_art.get_size()
        if art_width > 0 and art_height > 0:
            scale = (
                min(panel_width / art_width, panel_height / art_height)
                if plan["panelArtFit"] == "contain"
                else max(panel_width / art_width, panel_height / art_height)
            )
            scaled = get_cached_transformed_surface(
                get_runtime_surface_cache(runtime),
                pygame,
                panel_art,
                (max(1, int(art_width * scale)), max(1, int(art_height * scale))),
                namespace="dialog-panel-art",
            ).copy()
            scaled.set_alpha(int(round(int(plan["panelArtOpacity"]) * 2.55)))
            panel_surface.blit(scaled, scaled.get_rect(center=panel_rect.center))

    mask_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(mask_surface, (255, 255, 255, 255), mask_surface.get_rect(), border_radius=radius)
    panel_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    if plan["borderWidth"] > 0 and plan["borderOpacity"] > 0:
        border_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(
            border_surface,
            with_alpha(plan["borderColor"], int(plan["borderOpacity"])),
            border_surface.get_rect(),
            width=int(plan["borderWidth"]),
            border_radius=radius,
        )
        panel_surface.blit(border_surface, (0, 0))

    composed.blit(panel_surface, panel_origin)
    return composed


def render_runtime_dialog_panel(runtime, rect) -> None:
    plan = build_dialog_panel_render_plan(runtime, rect)
    surface = get_runtime_surface_cache(runtime).get_or_create(
        plan["cacheKey"],
        lambda: build_dialog_panel_surface(runtime, plan),
    )
    runtime.screen.blit(surface, plan["surfacePosition"])


__all__ = [
    "DIALOG_PANEL_CACHE_VERSION",
    "build_dialog_panel_render_plan",
    "build_dialog_panel_surface",
    "render_runtime_dialog_panel",
]
