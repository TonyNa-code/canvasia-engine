from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Callable
from uuid import uuid4


SAVE_ROOT_DIR_NAME = ".canvasia-engine"
SAVE_THUMBNAIL_SUBDIR_NAME = "native-runtime-save-thumbnails"
SAVE_THUMBNAIL_VERSION = 1
SAVE_THUMBNAIL_WIDTH = 320
SAVE_THUMBNAIL_HEIGHT = 180
_THUMBNAIL_KEY_PATTERN = re.compile(r"^(?:quick|formal-[0-9]{4})(?:-[0-9a-f]{12})?$")


def make_safe_project_storage_stem(project_id: str) -> str:
    clean = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in str(project_id or "")
    )
    return clean.strip("_") or "untitled_project"


def get_runtime_save_thumbnail_root(root_dir: Path | None = None) -> Path:
    if root_dir is not None:
        return Path(root_dir)
    return Path.home() / SAVE_ROOT_DIR_NAME / SAVE_THUMBNAIL_SUBDIR_NAME


def get_project_save_thumbnail_dir(project_id: str, root_dir: Path | None = None) -> Path:
    return get_runtime_save_thumbnail_root(root_dir) / make_safe_project_storage_stem(project_id)


def get_save_thumbnail_key(kind: str, slot_index: int | None = None) -> str:
    safe_kind = str(kind or "").strip().lower()
    if safe_kind == "quick":
        return "quick"
    if safe_kind != "formal":
        raise ValueError(f"Unsupported save thumbnail kind: {kind}")
    try:
        safe_slot_index = int(slot_index)
    except (TypeError, ValueError) as error:
        raise ValueError("Formal save thumbnails require a non-negative slot index.") from error
    if safe_slot_index < 0 or safe_slot_index > 9999:
        raise ValueError("Formal save thumbnail slot index is out of range.")
    return f"formal-{safe_slot_index + 1:04d}"


def create_versioned_save_thumbnail_key(kind: str, slot_index: int | None = None) -> str:
    return f"{get_save_thumbnail_key(kind, slot_index)}-{uuid4().hex[:12]}"


def is_safe_save_thumbnail_key(value: object) -> bool:
    return bool(_THUMBNAIL_KEY_PATTERN.fullmatch(str(value or "").strip()))


def get_save_thumbnail_path(project_id: str, thumbnail_key: str, root_dir: Path | None = None) -> Path:
    safe_key = str(thumbnail_key or "").strip()
    if not is_safe_save_thumbnail_key(safe_key):
        raise ValueError("Invalid save thumbnail key.")
    return get_project_save_thumbnail_dir(project_id, root_dir) / f"{safe_key}.png"


def resolve_snapshot_thumbnail_path(
    snapshot: dict | None,
    project_id: str,
    root_dir: Path | None = None,
    *,
    require_file: bool = True,
) -> Path | None:
    source = snapshot if isinstance(snapshot, dict) else {}
    thumbnail_key = str(source.get("thumbnailKey") or "").strip()
    if not is_safe_save_thumbnail_key(thumbnail_key):
        return None
    thumbnail_path = get_save_thumbnail_path(project_id, thumbnail_key, root_dir)
    if require_file and (not thumbnail_path.is_file() or thumbnail_path.stat().st_size <= 0):
        return None
    return thumbnail_path


def build_save_thumbnail_metadata(
    thumbnail_key: str,
    *,
    width: int = SAVE_THUMBNAIL_WIDTH,
    height: int = SAVE_THUMBNAIL_HEIGHT,
    captured_at: str | None = None,
) -> dict:
    if not is_safe_save_thumbnail_key(thumbnail_key):
        raise ValueError("Invalid save thumbnail key.")
    return {
        "thumbnailKey": str(thumbnail_key),
        "thumbnailVersion": SAVE_THUMBNAIL_VERSION,
        "thumbnailWidth": max(1, int(width or SAVE_THUMBNAIL_WIDTH)),
        "thumbnailHeight": max(1, int(height or SAVE_THUMBNAIL_HEIGHT)),
        "thumbnailCapturedAt": str(captured_at or datetime.now().astimezone().isoformat(timespec="seconds")),
    }


def calculate_cover_geometry(
    source_width: int,
    source_height: int,
    target_width: int = SAVE_THUMBNAIL_WIDTH,
    target_height: int = SAVE_THUMBNAIL_HEIGHT,
) -> dict:
    safe_source_width = max(1, int(source_width or 1))
    safe_source_height = max(1, int(source_height or 1))
    safe_target_width = max(1, int(target_width or 1))
    safe_target_height = max(1, int(target_height or 1))
    scale = max(safe_target_width / safe_source_width, safe_target_height / safe_source_height)
    scaled_width = max(safe_target_width, int(round(safe_source_width * scale)))
    scaled_height = max(safe_target_height, int(round(safe_source_height * scale)))
    return {
        "targetWidth": safe_target_width,
        "targetHeight": safe_target_height,
        "scaledWidth": scaled_width,
        "scaledHeight": scaled_height,
        "offsetX": (safe_target_width - scaled_width) // 2,
        "offsetY": (safe_target_height - scaled_height) // 2,
    }


def build_pygame_save_thumbnail_surface(
    pygame,
    source_surface,
    width: int = SAVE_THUMBNAIL_WIDTH,
    height: int = SAVE_THUMBNAIL_HEIGHT,
):
    source_width, source_height = source_surface.get_size()
    geometry = calculate_cover_geometry(source_width, source_height, width, height)
    scaled_surface = pygame.transform.smoothscale(
        source_surface,
        (geometry["scaledWidth"], geometry["scaledHeight"]),
    )
    thumbnail_surface = pygame.Surface(
        (geometry["targetWidth"], geometry["targetHeight"]),
        pygame.SRCALPHA,
    )
    thumbnail_surface.blit(scaled_surface, (geometry["offsetX"], geometry["offsetY"]))
    return thumbnail_surface


def capture_pygame_save_thumbnail(
    pygame,
    source_surface,
    project_id: str,
    thumbnail_key: str,
    root_dir: Path | None = None,
) -> tuple[Path, dict]:
    target_path = get_save_thumbnail_path(project_id, thumbnail_key, root_dir)
    thumbnail_surface = build_pygame_save_thumbnail_surface(pygame, source_surface)
    write_save_thumbnail_atomic(
        target_path,
        lambda temporary_path: pygame.image.save(thumbnail_surface, str(temporary_path)),
    )
    width, height = thumbnail_surface.get_size()
    return target_path, build_save_thumbnail_metadata(thumbnail_key, width=width, height=height)


def draw_pygame_save_thumbnail(
    pygame,
    target_surface,
    image,
    rect,
    *,
    panel_color: tuple[int, int, int],
    border_color: tuple[int, int, int],
    muted_color: tuple[int, int, int],
    label_font,
    empty_label: str = "No preview",
) -> bool:
    background = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(background, (*panel_color, 132), background.get_rect(), border_radius=12)
    target_surface.blit(background, rect.topleft)
    if image:
        preview = build_pygame_save_thumbnail_surface(pygame, image, rect.width, rect.height)
        mask = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=12)
        preview.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        target_surface.blit(preview, rect.topleft)
    else:
        label_surface = label_font.render(str(empty_label or ""), True, muted_color)
        target_surface.blit(label_surface, label_surface.get_rect(center=rect.center))
    pygame.draw.rect(target_surface, (*border_color, 112), rect, 1, border_radius=12)
    return bool(image)


def write_save_thumbnail_atomic(target_path: Path, writer: Callable[[Path], object]) -> Path:
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target.with_name(f".{target.stem}.{uuid4().hex}.tmp{target.suffix}")
    try:
        writer(temp_path)
        if not temp_path.is_file() or temp_path.stat().st_size <= 0:
            raise OSError("Save thumbnail writer did not create a usable image.")
        os.replace(temp_path, target)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return target


def get_referenced_save_thumbnail_keys(save_store: dict | None) -> set[str]:
    source = save_store if isinstance(save_store, dict) else {}
    snapshots = [source.get("quickSave"), *(source.get("formalSlots") or [])]
    return {
        str(snapshot.get("thumbnailKey"))
        for snapshot in snapshots
        if isinstance(snapshot, dict) and is_safe_save_thumbnail_key(snapshot.get("thumbnailKey"))
    }


def build_save_thumbnail_status(
    save_store: dict | None,
    project_id: str,
    root_dir: Path | None = None,
) -> dict:
    referenced_keys = sorted(get_referenced_save_thumbnail_keys(save_store))
    available_keys: list[str] = []
    missing_keys: list[str] = []
    for thumbnail_key in referenced_keys:
        thumbnail_path = get_save_thumbnail_path(project_id, thumbnail_key, root_dir)
        if thumbnail_path.is_file() and thumbnail_path.stat().st_size > 0:
            available_keys.append(thumbnail_key)
        else:
            missing_keys.append(thumbnail_key)
    return {
        "referencedCount": len(referenced_keys),
        "availableCount": len(available_keys),
        "missingCount": len(missing_keys),
        "referencedKeys": referenced_keys,
        "availableKeys": available_keys,
        "missingKeys": missing_keys,
    }


def prune_orphaned_save_thumbnails(
    save_store: dict | None,
    project_id: str,
    root_dir: Path | None = None,
) -> list[Path]:
    project_dir = get_project_save_thumbnail_dir(project_id, root_dir)
    if not project_dir.is_dir():
        return []
    referenced_keys = get_referenced_save_thumbnail_keys(save_store)
    removed: list[Path] = []
    for path in project_dir.glob("*.png"):
        if not is_safe_save_thumbnail_key(path.stem) or path.stem in referenced_keys:
            continue
        try:
            path.unlink()
        except OSError:
            continue
        removed.append(path)
    return removed
