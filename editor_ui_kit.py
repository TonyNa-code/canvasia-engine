from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy


UI_KIT_MAX_ASSET_COUNT = 12
UI_KIT_MAX_ASSET_BYTES = 12 * 1024 * 1024
UI_KIT_MAX_TOTAL_ASSET_BYTES = 32 * 1024 * 1024
UI_KIT_ALLOWED_ASSET_TYPES = frozenset({"background", "cg", "font", "sprite", "ui"})
UI_KIT_BINDING_RULES = {
    "gameUiConfig.fontAssetId": frozenset({"font"}),
    "gameUiConfig.titleBackgroundAssetId": frozenset({"background", "cg", "ui"}),
    "gameUiConfig.titleLogoAssetId": frozenset({"cg", "sprite", "ui"}),
    "gameUiConfig.panelFrameAssetId": frozenset({"ui"}),
    "gameUiConfig.buttonFrameAssetId": frozenset({"ui"}),
    "gameUiConfig.buttonHoverFrameAssetId": frozenset({"ui"}),
    "gameUiConfig.buttonPressedFrameAssetId": frozenset({"ui"}),
    "gameUiConfig.buttonDisabledFrameAssetId": frozenset({"ui"}),
    "gameUiConfig.saveSlotFrameAssetId": frozenset({"ui"}),
    "gameUiConfig.systemPanelFrameAssetId": frozenset({"ui"}),
    "gameUiConfig.uiOverlayAssetId": frozenset({"ui"}),
    "dialogBoxConfig.panelAssetId": frozenset({"ui"}),
}


def normalize_ui_kit_name(value: object) -> str:
    return str(value or "Canvasia UI Kit").strip()[:80] or "Canvasia UI Kit"


def normalize_ui_kit_file_descriptors(value: object) -> list[dict]:
    if not isinstance(value, list):
        raise ValueError("UI Kit 素材清单不是有效列表。")
    if len(value) > UI_KIT_MAX_ASSET_COUNT:
        raise ValueError(f"UI Kit 最多包含 {UI_KIT_MAX_ASSET_COUNT} 个素材。")

    normalized: list[dict] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"UI Kit 第 {index} 个素材描述无效。")
        asset_type = str(item.get("assetType") or "").strip()
        if asset_type not in UI_KIT_ALLOWED_ASSET_TYPES:
            raise ValueError(f"UI Kit 第 {index} 个素材类型不受支持：{asset_type or '空'}。")
        normalized.append(dict(item))
    return normalized


def normalize_ui_kit_bindings(value: object, file_count: int) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ValueError("UI Kit 素材绑定表不是有效对象。")

    normalized: dict[str, int] = {}
    for raw_path, raw_index in value.items():
        path = str(raw_path or "").strip()
        if path not in UI_KIT_BINDING_RULES:
            raise ValueError(f"UI Kit 包含未知的界面绑定：{path or '空'}。")
        if isinstance(raw_index, bool):
            raise ValueError(f"UI Kit 的 {path} 素材序号无效。")
        try:
            index = int(raw_index)
        except (TypeError, ValueError) as error:
            raise ValueError(f"UI Kit 的 {path} 素材序号无效。") from error
        if index < 0 or index >= file_count:
            raise ValueError(f"UI Kit 的 {path} 素材序号超出文件清单。")
        normalized[path] = index

    if set(normalized.values()) != set(range(file_count)):
        raise ValueError("UI Kit 存在没有绑定到任何界面部件的素材。")
    return normalized


def _split_binding_path(path: str) -> tuple[str, str]:
    group, field = path.split(".", 1)
    return group, field


def build_ui_kit_import_plan(
    *,
    game_ui_config: object,
    dialog_box_config: object,
    bindings: object,
    imported_assets: object,
) -> dict:
    game_ui = deepcopy(game_ui_config) if isinstance(game_ui_config, dict) else {}
    dialog_box = deepcopy(dialog_box_config) if isinstance(dialog_box_config, dict) else {}
    if not isinstance(imported_assets, list):
        raise ValueError("UI Kit 素材导入结果不是有效列表。")
    assets = imported_assets
    normalized_bindings = normalize_ui_kit_bindings(bindings, len(assets))
    config_groups = {
        "gameUiConfig": game_ui,
        "dialogBoxConfig": dialog_box,
    }

    for path in UI_KIT_BINDING_RULES:
        group, field = _split_binding_path(path)
        source_asset_id = str(config_groups[group].get(field) or "").strip()
        if source_asset_id and path not in normalized_bindings:
            raise ValueError(f"UI Kit 缺少 {path} 对应的素材文件。")
        if path in normalized_bindings and not source_asset_id:
            raise ValueError(f"UI Kit 的 {path} 绑定没有对应的源素材标识。")

    applied_bindings: dict[str, str] = {}
    for path, asset_index in normalized_bindings.items():
        asset = assets[asset_index]
        if not isinstance(asset, dict):
            raise ValueError(f"UI Kit 的 {path} 导入结果无效。")
        asset_id = str(asset.get("id") or "").strip()
        asset_type = str(asset.get("type") or "").strip()
        if not asset_id:
            raise ValueError(f"UI Kit 的 {path} 素材没有生成项目 ID。")
        if asset_type not in UI_KIT_BINDING_RULES[path]:
            raise ValueError(f"UI Kit 的 {path} 不能绑定 {asset_type or '未知'} 类型素材。")
        group, field = _split_binding_path(path)
        config_groups[group][field] = asset_id
        applied_bindings[path] = asset_id

    return {
        "gameUiConfig": game_ui,
        "dialogBoxConfig": dialog_box,
        "appliedBindings": applied_bindings,
        "assetCount": len(assets),
        "bindingCount": len(applied_bindings),
    }


def prepare_ui_kit_import(
    payload: object,
    *,
    decode_file: Callable[[dict], tuple[str, bytes]],
    is_file_allowed: Callable[[str, str], bool],
    asset_type_labels: Mapping[str, str] | None = None,
) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("UI Kit 导入请求不是有效对象。")

    name = normalize_ui_kit_name(payload.get("name"))
    files = normalize_ui_kit_file_descriptors(payload.get("files"))
    bindings = normalize_ui_kit_bindings(payload.get("bindings"), len(files))
    game_ui_config = payload.get("gameUiConfig") if isinstance(payload.get("gameUiConfig"), dict) else {}
    dialog_box_config = payload.get("dialogBoxConfig") if isinstance(payload.get("dialogBoxConfig"), dict) else {}
    labels = asset_type_labels or {}
    total_asset_bytes = 0
    preview_assets: list[dict] = []

    for index, file_item in enumerate(files):
        file_name, raw = decode_file(file_item)
        asset_type = str(file_item.get("assetType") or "").strip()
        size_bytes = len(raw)
        if size_bytes <= 0:
            raise ValueError(f"UI Kit 素材“{file_name}”是空文件。")
        if size_bytes > UI_KIT_MAX_ASSET_BYTES:
            raise ValueError(f"UI Kit 素材“{file_name}”超过单文件大小上限。")
        if not is_file_allowed(asset_type, file_name):
            raise ValueError(f"UI Kit 素材“{file_name}”不能作为{labels.get(asset_type, '当前')}类型导入。")
        total_asset_bytes += size_bytes
        preview_assets.append({"id": f"pending_ui_kit_asset_{index}", "type": asset_type})

    if total_asset_bytes > UI_KIT_MAX_TOTAL_ASSET_BYTES:
        raise ValueError("UI Kit 素材总大小超过安全上限。")

    build_ui_kit_import_plan(
        game_ui_config=game_ui_config,
        dialog_box_config=dialog_box_config,
        bindings=bindings,
        imported_assets=preview_assets,
    )
    return {
        "name": name,
        "files": files,
        "bindings": bindings,
        "gameUiConfig": game_ui_config,
        "dialogBoxConfig": dialog_box_config,
        "totalAssetBytes": total_asset_bytes,
    }


__all__ = [
    "UI_KIT_ALLOWED_ASSET_TYPES",
    "UI_KIT_BINDING_RULES",
    "UI_KIT_MAX_ASSET_BYTES",
    "UI_KIT_MAX_ASSET_COUNT",
    "UI_KIT_MAX_TOTAL_ASSET_BYTES",
    "build_ui_kit_import_plan",
    "normalize_ui_kit_bindings",
    "normalize_ui_kit_file_descriptors",
    "normalize_ui_kit_name",
    "prepare_ui_kit_import",
]
