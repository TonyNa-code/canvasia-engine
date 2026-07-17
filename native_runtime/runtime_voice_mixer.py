from __future__ import annotations

from collections.abc import Callable, Iterable


NARRATOR_VOICE_PROFILE_ID = "__canvasia_narrator__"
MAX_VOICE_PROFILE_COUNT = 160
MAX_VOICE_PROFILE_ID_LENGTH = 128
BLOCKED_VOICE_PROFILE_IDS = {"__proto__", "prototype", "constructor"}


def _with_alpha(color: object, opacity_percent: object) -> tuple[int, int, int, int]:
    values = tuple(color) if isinstance(color, (tuple, list)) else (0, 0, 0)
    red, green, blue = (int(values[index]) if len(values) > index else 0 for index in range(3))
    alpha = _safe_volume_percent(opacity_percent, 100)
    return red, green, blue, int(round(alpha * 2.55))


def _safe_volume_percent(value: object, fallback: int = 100) -> int:
    try:
        numeric = int(round(float(value)))
    except Exception:
        numeric = fallback
    return max(0, min(100, numeric))


def get_safe_voice_profile_id(value: object) -> str:
    profile_id = str(value or "").strip()
    if (
        not profile_id
        or len(profile_id) > MAX_VOICE_PROFILE_ID_LENGTH
        or profile_id in BLOCKED_VOICE_PROFILE_IDS
        or any(ord(character) < 32 or ord(character) == 127 for character in profile_id)
    ):
        return ""
    return profile_id


def sanitize_voice_mix_profiles(
    source: object,
    allowed_ids: Iterable[object] | None = None,
) -> dict[str, dict[str, object]]:
    if not isinstance(source, dict):
        return {}
    safe_allowed_ids = None
    if allowed_ids is not None:
        safe_allowed_ids = {profile_id for item in allowed_ids if (profile_id := get_safe_voice_profile_id(item))}

    result: dict[str, dict[str, object]] = {}
    for raw_profile_id, raw_profile in source.items():
        if len(result) >= MAX_VOICE_PROFILE_COUNT:
            break
        profile_id = get_safe_voice_profile_id(raw_profile_id)
        if not profile_id or (safe_allowed_ids is not None and profile_id not in safe_allowed_ids):
            continue
        if isinstance(raw_profile, (int, float, str)):
            profile = {"volume": raw_profile}
        elif isinstance(raw_profile, dict):
            profile = raw_profile
        else:
            profile = {}
        result[profile_id] = {
            "volume": _safe_volume_percent(profile.get("volume"), 100),
            "muted": profile.get("muted") is True,
        }
    return result


def get_voice_mix_profile(profiles: object, profile_id: object) -> dict[str, object]:
    safe_profile_id = get_safe_voice_profile_id(profile_id)
    if not safe_profile_id:
        return {"volume": 100, "muted": False}
    safe_profiles = sanitize_voice_mix_profiles(profiles)
    return dict(safe_profiles.get(safe_profile_id) or {"volume": 100, "muted": False})


def get_voice_mix_volume_ratio(profiles: object, profile_id: object) -> float:
    profile = get_voice_mix_profile(profiles, profile_id)
    if profile["muted"]:
        return 0.0
    return int(profile["volume"]) / 100


def update_voice_mix_profile(
    profiles: object,
    profile_id: object,
    *,
    volume: object | None = None,
    muted: bool | None = None,
) -> dict[str, dict[str, object]]:
    safe_profiles = sanitize_voice_mix_profiles(profiles)
    safe_profile_id = get_safe_voice_profile_id(profile_id)
    if not safe_profile_id:
        return safe_profiles
    current = get_voice_mix_profile(safe_profiles, safe_profile_id)
    next_profile = {
        "volume": _safe_volume_percent(volume, int(current["volume"])) if volume is not None else int(current["volume"]),
        "muted": muted if isinstance(muted, bool) else bool(current["muted"]),
    }
    if next_profile == {"volume": 100, "muted": False}:
        safe_profiles.pop(safe_profile_id, None)
    else:
        safe_profiles[safe_profile_id] = next_profile
    return safe_profiles


def get_voice_profile_id_from_block(block: object) -> str:
    if not isinstance(block, dict):
        return ""
    block_type = str(block.get("type") or "").strip()
    if block_type == "narration":
        return NARRATOR_VOICE_PROFILE_ID
    if block_type == "dialogue":
        return get_safe_voice_profile_id(block.get("speakerId"))
    return ""


def collect_voice_mixer_entries(
    chapters: object,
    characters_by_id: object,
    get_character_name: Callable[[str, dict], str] | None = None,
    narrator_label: str = "旁白",
) -> list[dict[str, object]]:
    safe_chapters = chapters if isinstance(chapters, list) else []
    character_map = characters_by_id if isinstance(characters_by_id, dict) else {}
    entries_by_id: dict[str, dict[str, object]] = {}

    for chapter in safe_chapters:
        if not isinstance(chapter, dict):
            continue
        for scene in chapter.get("scenes") or []:
            if not isinstance(scene, dict):
                continue
            scene_id = str(scene.get("id") or "").strip()
            for block in scene.get("blocks") or []:
                if (
                    not isinstance(block, dict)
                    or not block.get("voiceAssetId")
                    or block.get("type") not in {"dialogue", "narration"}
                ):
                    continue
                profile_id = get_voice_profile_id_from_block(block)
                if not profile_id:
                    continue
                if profile_id not in entries_by_id:
                    character = character_map.get(profile_id) if profile_id != NARRATOR_VOICE_PROFILE_ID else {}
                    if not isinstance(character, dict):
                        character = {}
                    label = narrator_label
                    if profile_id != NARRATOR_VOICE_PROFILE_ID:
                        label = (
                            get_character_name(profile_id, character)
                            if get_character_name
                            else str(character.get("displayName") or character.get("name") or profile_id)
                        )
                    entries_by_id[profile_id] = {
                        "id": profile_id,
                        "label": str(label or profile_id),
                        "lineCount": 0,
                        "sceneIds": set(),
                    }
                entry = entries_by_id[profile_id]
                entry["lineCount"] = int(entry["lineCount"]) + 1
                if scene_id:
                    entry["sceneIds"].add(scene_id)

    return [
        {
            "id": entry["id"],
            "label": entry["label"],
            "lineCount": entry["lineCount"],
            "sceneCount": len(entry["sceneIds"]),
        }
        for entry in entries_by_id.values()
    ]


def get_voice_mixer_summary(entries: object, profiles: object) -> dict[str, int]:
    safe_entries = entries if isinstance(entries, list) else []
    customized_count = 0
    muted_count = 0
    for entry in safe_entries:
        profile_id = entry.get("id") if isinstance(entry, dict) else ""
        profile = get_voice_mix_profile(profiles, profile_id)
        if profile["muted"] or profile["volume"] != 100:
            customized_count += 1
        if profile["muted"]:
            muted_count += 1
    return {
        "characterCount": len(safe_entries),
        "customizedCount": customized_count,
        "mutedCount": muted_count,
    }


def render_voice_mixer_overlay(player: object) -> None:
    """Render the native mixer while keeping its feature UI out of the main player loop."""
    palette = player.get_active_palette()
    entries = player.get_voice_mixer_entries()
    summary = get_voice_mixer_summary(entries, player.runtime_settings.get("voiceMix"))
    panel = player.pygame.Rect(0, 0, min(player.width - 72, 860), min(player.height - 64, 590))
    panel.center = (player.width // 2, player.height // 2)
    player.pygame.draw.rect(player.screen, (*palette["panel"], 246), panel, border_radius=28)
    player.pygame.draw.rect(
        player.screen,
        _with_alpha(palette["panelBorder"], 72),
        panel,
        2,
        border_radius=28,
    )
    player.draw_game_ui_panel_frame(panel, "system")
    player.screen.blit(
        player.font_title.render("角色语音混音", True, palette["text"]),
        (panel.left + 28, panel.top + 24),
    )
    summary_text = (
        f"{summary['characterCount']} 个语音通道 · 已单独调整 {summary['customizedCount']} 个 · 已静音 {summary['mutedCount']} 个"
        if entries
        else "项目中还没有绑定语音的角色或旁白。"
    )
    player.screen.blit(
        player.font_ui.render(summary_text, True, palette["muted"]),
        (panel.left + 28, panel.top + 62),
    )

    reset_rect = player.pygame.Rect(panel.right - 202, panel.top + 24, 174, 34)
    player.pygame.draw.rect(player.screen, _with_alpha(palette["panel"], 54), reset_rect, border_radius=14)
    player.pygame.draw.rect(player.screen, _with_alpha(palette["panelBorder"], 42), reset_rect, 1, border_radius=14)
    player.draw_game_ui_button_frame(reset_rect, player.get_game_ui_button_state(reset_rect))
    player.blit_text_center(player.font_ui, "全部跟随总音量", reset_rect.centerx, reset_rect.top + 8, palette["text"])
    player.overlay_hotspots.append({"kind": "voice-mixer-reset-all", "rect": reset_rect})

    if entries:
        visible_count = max(1, min(8, (panel.height - 160) // 54))
        max_start = max(0, len(entries) - visible_count)
        visible_start = max(0, min(max_start, player.voice_mixer_index - visible_count + 1))
        for offset, entry in enumerate(entries[visible_start : visible_start + visible_count]):
            index = visible_start + offset
            row_rect = player.pygame.Rect(panel.left + 24, panel.top + 98 + offset * 54, panel.width - 48, 44)
            is_active = index == player.voice_mixer_index
            profile = get_voice_mix_profile(player.runtime_settings.get("voiceMix"), entry.get("id"))
            player.pygame.draw.rect(
                player.screen,
                _with_alpha(palette["accent" if is_active else "panel"], 68 if is_active else 30),
                row_rect,
                border_radius=16,
            )
            player.pygame.draw.rect(
                player.screen,
                _with_alpha(palette["accentAlt" if is_active else "panelBorder"], 82 if is_active else 22),
                row_rect,
                1,
                border_radius=16,
            )
            player.draw_game_ui_button_frame(
                row_rect,
                player.get_game_ui_button_state(row_rect, active=is_active),
            )
            player.screen.blit(
                player.font_ui.render(str(entry.get("label") or "未命名角色")[:24], True, palette["text"]),
                (row_rect.left + 14, row_rect.top + 7),
            )
            detail = f"{entry.get('lineCount') or 0} 句 · {entry.get('sceneCount') or 0} 场"
            player.screen.blit(
                player.font_ui.render(detail, True, palette["muted"]),
                (row_rect.left + 14, row_rect.top + 24),
            )

            volume_label = "静音" if profile["muted"] else f"{profile['volume']}%"
            volume_color = palette["muted"] if profile["muted"] else palette["accent"]
            volume_surface = player.font_ui.render(volume_label, True, volume_color)
            player.screen.blit(volume_surface, (row_rect.right - 234, row_rect.top + 13))
            control_specs = (
                ("voice-mixer-dec", "−", 42),
                ("voice-mixer-mute", "恢复" if profile["muted"] else "静音", 72),
                ("voice-mixer-inc", "+", 42),
            )
            control_left = row_rect.right - 168
            for kind, label, width in control_specs:
                control_rect = player.pygame.Rect(control_left, row_rect.top + 5, width, 34)
                player.pygame.draw.rect(player.screen, _with_alpha(palette["panel"], 58), control_rect, border_radius=13)
                player.pygame.draw.rect(
                    player.screen,
                    _with_alpha(palette["panelBorder"], 38),
                    control_rect,
                    1,
                    border_radius=13,
                )
                player.draw_game_ui_button_frame(control_rect, player.get_game_ui_button_state(control_rect))
                player.blit_text_center(player.font_ui, label, control_rect.centerx, control_rect.top + 8, palette["text"])
                player.overlay_hotspots.append({"kind": kind, "index": index, "rect": control_rect})
                control_left += width + 6
            player.overlay_hotspots.append({"kind": "voice-mixer-select", "index": index, "rect": row_rect})
    else:
        empty_rect = player.pygame.Rect(panel.left + 28, panel.top + 112, panel.width - 56, 120)
        player.pygame.draw.rect(player.screen, _with_alpha(palette["panel"], 34), empty_rect, border_radius=20)
        player.blit_text_center(
            player.font_body,
            "先在剧情台词或旁白中绑定语音素材",
            empty_rect.centerx,
            empty_rect.top + 40,
            palette["muted"],
        )

    hint = "↑↓ 选择 · ←→ 调音量 · Enter/M 静音 · R 重置当前 · Esc 返回"
    player.screen.blit(player.font_ui.render(hint, True, palette["muted"]), (panel.left + 28, panel.bottom - 44))
