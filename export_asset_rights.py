from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path


EXPORT_ASSET_RIGHTS_JSON_NAME = "asset-rights-manifest.json"
EXPORT_ASSET_RIGHTS_REPORT_NAME = "asset-rights-report.md"
EXPORT_ASSET_RIGHTS_CSV_NAME = "asset-rights-table.csv"

ASSET_TYPE_LABELS = {
    "background": "背景",
    "sprite": "立绘",
    "cg": "CG",
    "bgm": "音乐",
    "sfx": "音效",
    "voice": "语音",
    "video": "视频",
    "ui": "界面素材",
    "font": "字体",
    "live2d": "Live2D",
    "model3d": "3D 模型",
    "scene3d": "3D 场景",
}
BLOCK_LABELS = {
    "background": "切换背景",
    "dialogue": "台词",
    "narration": "旁白",
    "character_show": "显示角色",
    "character_hide": "隐藏角色",
    "music_play": "播放音乐",
    "music_stop": "停止音乐",
    "sfx_play": "播放音效",
    "video_play": "播放视频",
    "credits_roll": "片尾字幕",
    "particle_effect": "粒子特效",
    "screen_shake": "屏幕震动",
    "screen_flash": "闪屏",
    "screen_fade": "黑场淡入淡出",
    "camera_zoom": "镜头推近拉远",
    "camera_pan": "镜头平移",
    "screen_filter": "画面滤镜",
}

PLACEHOLDER_RE = re.compile(r"(placeholder|sample|demo|temp|tmp|dummy|占位|示例|测试|临时)", re.I)
NON_COMMERCIAL_RE = re.compile(
    r"(non[-_\s]?commercial|cc[-_\s]?by[-_\s]?nc|personal only|editorial|不可商用|非商用|个人使用|禁止商用)",
    re.I,
)
ATTRIBUTION_RE = re.compile(r"(cc[-_\s]?by|attribution|署名|标注作者|需署名|credit required)", re.I)
AI_PROVENANCE_RE = re.compile(r"(openai|midjourney|stable diffusion|sdxl|novelai|dall|sora|ai|人工智能|生成)", re.I)


def clean_text(value: object, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text or fallback


def to_bool_or_none(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    text = clean_text(value).lower()
    if text in {"true", "yes", "allowed", "ok", "commercial", "可商用", "允许", "允许商用"}:
        return True
    if text in {"false", "no", "forbidden", "not allowed", "noncommercial", "不可商用", "禁止", "非商用"}:
        return False
    return None


def get_nested_value(source: dict, key: str) -> object:
    if key in source:
        return source.get(key)
    for nested_key in ("meta", "rights", "provenance"):
        nested = source.get(nested_key)
        if isinstance(nested, dict) and key in nested:
            return nested.get(key)
    return None


def first_text(source: dict, keys: list[str], fallback: str = "") -> str:
    for key in keys:
        value = get_nested_value(source, key)
        if isinstance(value, list):
            text = " / ".join(clean_text(item) for item in value if clean_text(item))
        else:
            text = clean_text(value)
        if text:
            return text
    return fallback


def first_bool(source: dict, keys: list[str]) -> bool | None:
    for key in keys:
        value = get_nested_value(source, key)
        parsed = to_bool_or_none(value)
        if parsed is not None:
            return parsed
    return None


def normalize_character_presentation(source: object, fallback_sprite_asset_id: str = "") -> dict:
    payload = source if isinstance(source, dict) else {}
    live2d = payload.get("live2d") if isinstance(payload.get("live2d"), dict) else {}
    model3d = payload.get("model3d") if isinstance(payload.get("model3d"), dict) else {}
    return {
        "fallbackSpriteAssetId": clean_text(payload.get("fallbackSpriteAssetId") or fallback_sprite_asset_id),
        "live2d": {"modelAssetId": clean_text(live2d.get("modelAssetId"))},
        "model3d": {"modelAssetId": clean_text(model3d.get("modelAssetId"))},
    }


def collect_character_asset_entries(character: dict) -> list[tuple[str, str]]:
    display_name = clean_text(character.get("displayName") or character.get("id"), "未命名角色")
    entries: list[tuple[str, str]] = []

    default_sprite_id = clean_text(character.get("defaultSpriteId"))
    if default_sprite_id:
        entries.append((default_sprite_id, f"角色默认立绘：{display_name}"))

    presentation = normalize_character_presentation(character.get("presentation"), default_sprite_id)
    fallback_sprite_id = clean_text(presentation.get("fallbackSpriteAssetId"))
    if fallback_sprite_id:
        entries.append((fallback_sprite_id, f"角色高级表现兜底立绘：{display_name}"))
    live2d_asset_id = clean_text((presentation.get("live2d") or {}).get("modelAssetId"))
    if live2d_asset_id:
        entries.append((live2d_asset_id, f"角色Live2D 模型入口：{display_name}"))
    model3d_asset_id = clean_text((presentation.get("model3d") or {}).get("modelAssetId"))
    if model3d_asset_id:
        entries.append((model3d_asset_id, f"角色3D 模型入口：{display_name}"))

    for expression in character.get("expressions", []) or []:
        expression_name = clean_text(expression.get("name") or expression.get("id"), "表情")
        sprite_asset_id = clean_text(expression.get("spriteAssetId"))
        if sprite_asset_id:
            entries.append((sprite_asset_id, f"角色表情：{display_name} / {expression_name}"))
        for layer_asset_id in expression.get("layerAssetIds") or []:
            clean_asset_id = clean_text(layer_asset_id)
            if clean_asset_id:
                entries.append((clean_asset_id, f"角色差分图层：{display_name} / {expression_name}"))

    return entries


def build_asset_usage_index(bundle: dict) -> dict[str, list[str]]:
    usage_index: dict[str, list[str]] = {}
    characters = (bundle.get("characters") or {}).get("characters") or []
    characters_by_id = {character.get("id"): character for character in characters if character.get("id")}

    def add_usage(asset_id: object, label: str) -> None:
        clean_asset_id = clean_text(asset_id)
        clean_label = clean_text(label)
        if not clean_asset_id or not clean_label:
            return
        labels = usage_index.setdefault(clean_asset_id, [])
        if clean_label not in labels:
            labels.append(clean_label)

    for character in characters:
        for asset_id, label in collect_character_asset_entries(character):
            add_usage(asset_id, label)

    for chapter in bundle.get("chapters") or []:
        for scene in chapter.get("scenes") or []:
            scene_name = clean_text(scene.get("name"), "未命名场景")
            for block in scene.get("blocks") or []:
                block_type = clean_text(block.get("type"), "剧情卡片")
                add_usage(block.get("assetId"), f"场景：{scene_name} / {BLOCK_LABELS.get(block_type, block_type)}")
                add_usage(block.get("voiceAssetId"), f"场景：{scene_name} / 台词语音")
                if block_type in {"dialogue", "character_show"}:
                    character_id = clean_text(block.get("speakerId") or block.get("characterId"))
                    expression_id = clean_text(block.get("expressionId"))
                    character = characters_by_id.get(character_id)
                    if not character:
                        continue
                    for expression in character.get("expressions") or []:
                        if clean_text(expression.get("id")) != expression_id:
                            continue
                        expression_name = clean_text(expression.get("name") or expression_id, "表情")
                        add_usage(
                            expression.get("spriteAssetId"),
                            f"场景：{scene_name} / {clean_text(character.get('displayName') or character_id)} {expression_name}",
                        )
                        break

    return usage_index


def has_marker(asset: dict, pattern: re.Pattern[str]) -> bool:
    tags = " ".join(clean_text(tag) for tag in asset.get("tags") or [])
    haystack = " ".join(
        clean_text(item)
        for item in [
            asset.get("id"),
            asset.get("name"),
            asset.get("path"),
            asset.get("fileName"),
            tags,
            first_text(asset, ["note", "description"]),
        ]
        if clean_text(item)
    )
    return bool(pattern.search(haystack))


def is_placeholder_asset(asset: dict) -> bool:
    return has_marker(asset, PLACEHOLDER_RE)


def is_ai_generated_asset(asset: dict) -> bool:
    if first_bool(asset, ["generatedByAi", "aiGenerated", "isAiGenerated"]) is True:
        return True
    provider = first_text(asset, ["aiProvider", "provider", "generatedBy", "modelProvider"])
    prompt = first_text(asset, ["prompt", "generationPrompt", "sourcePrompt"])
    return bool(prompt or has_marker({**asset, "name": f"{asset.get('name') or ''} {provider}"}, AI_PROVENANCE_RE))


def get_commercial_status(asset: dict, license_label: str) -> dict:
    commercial_flag = first_bool(asset, ["commercialUse", "commercialAllowed", "allowCommercialUse", "isCommercialUseAllowed"])
    commercial_text = first_text(asset, ["commercialUse", "commercialAllowed", "usageRights", "rightsStatus", "terms"])
    label_source = f"{license_label} {commercial_text}"
    if commercial_flag is False or NON_COMMERCIAL_RE.search(label_source):
        return {"status": "blocked", "label": commercial_text or "不可商用 / 未获商用许可"}
    if commercial_flag is True or re.search(r"(commercial|royalty[-_\s]?free|可商用|商用可|允许商用)", label_source, re.I):
        return {"status": "ready", "label": commercial_text or "可商用"}
    return {"status": "unknown", "label": commercial_text or "未登记商用状态"}


def needs_attribution(asset: dict, license_label: str) -> bool:
    flag = first_bool(asset, ["attributionRequired", "creditRequired", "requiresCredit"])
    if flag is not None:
        return flag
    return bool(ATTRIBUTION_RE.search(f"{license_label} {first_text(asset, ['terms', 'usageRights'])}"))


def get_status_from_issues(issues: list[dict]) -> str:
    if any(issue.get("severity") == "blocker" for issue in issues):
        return "blocker"
    if any(issue.get("severity") == "warn" for issue in issues):
        return "warn"
    if issues:
        return "tip"
    return "good"


def get_issue_weight(issue: dict) -> int:
    return {"blocker": 100, "warn": 60, "tip": 20}.get(str(issue.get("severity")), 0)


def build_asset_rights_record(asset: dict, usage_index: dict[str, list[str]]) -> dict:
    asset_id = clean_text(asset.get("id"))
    license_label = first_text(asset, ["license", "licenseName", "licenseType", "licenseLabel", "rightsLicense"], "未登记")
    commercial = get_commercial_status(asset, license_label)
    usage_locations = usage_index.get(asset_id, [])
    record = {
        "assetId": asset_id,
        "assetName": clean_text(asset.get("name"), asset_id or "未命名素材"),
        "type": clean_text(asset.get("type"), "unknown"),
        "typeLabel": ASSET_TYPE_LABELS.get(clean_text(asset.get("type")), clean_text(asset.get("type"), "未知")),
        "path": clean_text(asset.get("path")),
        "exportUrl": clean_text(asset.get("exportUrl")),
        "fileExists": not bool(asset.get("isMissing")),
        "usageCount": len(usage_locations),
        "usageLocations": usage_locations,
        "licenseLabel": license_label,
        "sourceLabel": first_text(asset, ["sourceUrl", "sourceURL", "source", "origin", "assetSource", "downloadUrl"]),
        "authorLabel": first_text(asset, ["author", "creator", "artist", "copyrightOwner", "owner"]),
        "creditLabel": first_text(asset, ["credit", "attribution", "creditLine", "requiredCredit"]),
        "commercialLabel": commercial["label"],
        "commercialStatus": commercial["status"],
        "providerLabel": first_text(asset, ["aiProvider", "provider", "generatedBy", "modelProvider", "model"]),
        "promptLabel": first_text(asset, ["prompt", "generationPrompt", "sourcePrompt"]),
        "isPlaceholder": is_placeholder_asset(asset),
        "isAiGenerated": is_ai_generated_asset(asset),
        "attributionRequired": needs_attribution(asset, license_label),
        "issues": [],
        "status": "good",
    }
    evaluate_asset_rights_record(record)
    return record


def push_issue(record: dict, severity: str, code: str, title: str, detail: str) -> None:
    record["issues"].append(
        {
            "severity": severity,
            "code": code,
            "title": title,
            "detail": detail,
            "assetId": record["assetId"],
            "assetName": record["assetName"],
            "typeLabel": record["typeLabel"],
            "usageCount": record["usageCount"],
        }
    )


def evaluate_asset_rights_record(record: dict) -> None:
    is_used = int(record.get("usageCount") or 0) > 0
    missing_license = record.get("licenseLabel") == "未登记"
    missing_source = not record.get("sourceLabel") and not record.get("authorLabel")
    missing_credit = bool(record.get("attributionRequired")) and not record.get("creditLabel") and not record.get("authorLabel")

    if is_used and record.get("commercialStatus") == "blocked":
        push_issue(record, "blocker", "asset_rights_noncommercial", "已使用素材不可商用", f"{record['assetName']} 标记为 {record['commercialLabel']}，发布前需要替换或重新取得授权。")
    elif is_used and record.get("commercialStatus") == "unknown":
        push_issue(record, "warn", "asset_rights_commercial_unknown", "商用状态未确认", f"{record['assetName']} 已被项目使用，但没有登记是否允许商用。")

    if is_used and missing_license:
        push_issue(record, "warn", "asset_rights_license_missing", "缺少授权协议", f"{record['assetName']} 已被使用，建议登记许可证、购买凭证或自制说明。")
    elif not is_used and missing_license:
        push_issue(record, "tip", "asset_rights_unused_license_missing", "未使用素材缺授权记录", f"{record['assetName']} 暂未使用，但如果之后要进成品，最好先补授权信息。")

    if is_used and missing_source:
        push_issue(record, "warn", "asset_rights_source_missing", "缺少来源或作者", f"{record['assetName']} 没有登记来源链接、作者或自制记录，后续做 Staff / Credits 会很难追。")

    if is_used and missing_credit:
        push_issue(record, "warn", "asset_rights_credit_missing", "缺少署名文本", f"{record['assetName']} 的授权看起来需要署名，但还没有准备可直接放入 Staff 的 credit line。")

    if is_used and record.get("isPlaceholder"):
        push_issue(record, "warn", "asset_rights_placeholder_used", "占位素材仍在成品中", f"{record['assetName']} 像是占位 / 示例 / 临时素材，发布前建议替换为正式素材。")

    if is_used and record.get("isAiGenerated") and (not record.get("providerLabel") or not record.get("promptLabel")):
        push_issue(record, "warn", "asset_rights_ai_provenance_missing", "AI 生成来源不完整", f"{record['assetName']} 像是 AI 生成素材，建议记录模型 / 服务商 / prompt 关键词，方便之后复查。")

    record["status"] = get_status_from_issues(record["issues"])


def build_export_asset_rights_manifest(bundle: dict, assets_doc: dict) -> dict:
    assets = assets_doc.get("assets") if isinstance(assets_doc, dict) else []
    safe_assets = [asset for asset in (assets or []) if isinstance(asset, dict)]
    usage_index = build_asset_usage_index(bundle)
    records = [build_asset_rights_record(asset, usage_index) for asset in safe_assets]
    issues = [issue for record in records for issue in record["issues"]]
    records.sort(
        key=lambda record: (
            -max([get_issue_weight(issue) for issue in record["issues"]] or [0]),
            -int(record.get("usageCount") or 0),
            record.get("assetName") or "",
        )
    )
    issues.sort(key=lambda issue: (-get_issue_weight(issue), issue.get("assetName") or ""))
    used_records = [record for record in records if int(record.get("usageCount") or 0) > 0]
    blocker_count = sum(1 for issue in issues if issue.get("severity") == "blocker")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warn")
    tip_count = sum(1 for issue in issues if issue.get("severity") == "tip")
    readiness_penalty = min(100, blocker_count * 24 + warning_count * 8 + tip_count)
    credit_roll = [
        {
            "assetName": record["assetName"],
            "typeLabel": record["typeLabel"],
            "creditLine": clean_text(record.get("creditLabel") or " / ".join(filter(None, [record["assetName"], record.get("authorLabel"), record.get("sourceLabel")]))),
        }
        for record in used_records
        if record.get("creditLabel") or record.get("authorLabel") or record.get("sourceLabel")
    ]
    summary = {
        "assetCount": len(records),
        "usedAssetCount": len(used_records),
        "unusedAssetCount": len(records) - len(used_records),
        "missingLicenseCount": sum(1 for record in records if record.get("licenseLabel") == "未登记"),
        "usedMissingLicenseCount": sum(1 for record in used_records if record.get("licenseLabel") == "未登记"),
        "missingSourceCount": sum(1 for record in used_records if not record.get("sourceLabel") and not record.get("authorLabel")),
        "missingCreditCount": sum(1 for record in used_records if record.get("attributionRequired") and not record.get("creditLabel") and not record.get("authorLabel")),
        "placeholderCount": sum(1 for record in records if record.get("isPlaceholder")),
        "usedPlaceholderCount": sum(1 for record in used_records if record.get("isPlaceholder")),
        "aiGeneratedCount": sum(1 for record in records if record.get("isAiGenerated")),
        "aiProvenanceMissingCount": sum(1 for record in used_records if record.get("isAiGenerated") and (not record.get("providerLabel") or not record.get("promptLabel"))),
        "nonCommercialCount": sum(1 for record in used_records if record.get("commercialStatus") == "blocked"),
        "commercialUnknownCount": sum(1 for record in used_records if record.get("commercialStatus") == "unknown"),
        "blockerCount": blocker_count,
        "warningCount": warning_count,
        "tipCount": tip_count,
        "readinessPercent": max(0, 100 - readiness_penalty),
    }
    return {
        "formatVersion": 1,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "projectTitle": clean_text((bundle.get("project") or {}).get("title"), "Canvasia Project"),
        "summary": summary,
        "assets": records,
        "issues": issues,
        "creditRoll": credit_roll,
    }


def markdown_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", "<br />").strip()


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return ""
    return "\n".join(
        [
            f"| {' | '.join(markdown_cell(header) for header in headers)} |",
            f"| {' | '.join('---' for _ in headers)} |",
            *(f"| {' | '.join(markdown_cell(cell) for cell in row)} |" for row in rows),
        ]
    )


def build_export_asset_rights_report(manifest: dict) -> str:
    summary = manifest.get("summary") or {}
    issue_rows = [
        [issue.get("severity"), issue.get("title"), issue.get("assetName"), issue.get("detail")]
        for issue in (manifest.get("issues") or [])[:24]
    ]
    asset_rows = [
        [
            record.get("typeLabel"),
            record.get("assetName"),
            record.get("usageCount"),
            record.get("licenseLabel"),
            record.get("commercialLabel"),
            record.get("sourceLabel") or record.get("authorLabel") or "未登记",
            record.get("creditLabel") or "未登记",
        ]
        for record in (manifest.get("assets") or [])[:80]
    ]
    credit_rows = [
        [entry.get("typeLabel"), entry.get("assetName"), entry.get("creditLine")]
        for entry in (manifest.get("creditRoll") or [])[:80]
    ]
    lines = [
        "# 素材授权与署名随包报告",
        "",
        f"- 项目：{manifest.get('projectTitle') or 'Canvasia Project'}",
        f"- 生成时间：{manifest.get('generatedAt')}",
        f"- 发布就绪度：{summary.get('readinessPercent', 0)}%",
        f"- 已使用素材：{summary.get('usedAssetCount', 0)} / {summary.get('assetCount', 0)}",
        f"- 授权先修：{summary.get('blockerCount', 0)}，待补项：{summary.get('warningCount', 0)}，整理项：{summary.get('tipCount', 0)}",
        "",
        "## 优先处理",
        "",
        markdown_table(["级别", "问题", "素材", "说明"], issue_rows) or "暂时没有发现素材授权阻塞或待补项。",
        "",
        "## Staff / Credits 草稿",
        "",
        markdown_table(["类型", "素材", "署名文本"], credit_rows) or "还没有可直接放入 Staff 的署名记录。",
        "",
        "## 素材明细",
        "",
        markdown_table(["类型", "素材", "使用次数", "授权", "商用状态", "来源 / 作者", "署名"], asset_rows)
        or "素材库为空。",
        "",
    ]
    return "\n".join(lines)


def build_export_asset_rights_csv(manifest: dict) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["assetId", "assetName", "type", "usageCount", "license", "commercialUse", "source", "author", "credit", "generatedByAi", "issues"])
    for record in manifest.get("assets") or []:
        writer.writerow(
            [
                record.get("assetId"),
                record.get("assetName"),
                record.get("type"),
                record.get("usageCount"),
                record.get("licenseLabel"),
                record.get("commercialLabel"),
                record.get("sourceLabel"),
                record.get("authorLabel"),
                record.get("creditLabel"),
                "yes" if record.get("isAiGenerated") else "no",
                " / ".join(issue.get("code", "") for issue in record.get("issues") or []),
            ]
        )
    return output.getvalue()


def write_export_asset_rights_files(target_dir: Path, *, bundle: dict, assets_doc: dict) -> dict:
    manifest = build_export_asset_rights_manifest(bundle, assets_doc)
    json_path = target_dir / EXPORT_ASSET_RIGHTS_JSON_NAME
    report_path = target_dir / EXPORT_ASSET_RIGHTS_REPORT_NAME
    csv_path = target_dir / EXPORT_ASSET_RIGHTS_CSV_NAME
    json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(build_export_asset_rights_report(manifest), encoding="utf-8")
    csv_path.write_text(build_export_asset_rights_csv(manifest), encoding="utf-8")
    return {
        "assetRightsManifest": manifest,
        "assetRightsName": json_path.name,
        "assetRightsPath": str(json_path),
        "assetRightsReportName": report_path.name,
        "assetRightsReportPath": str(report_path),
        "assetRightsCsvName": csv_path.name,
        "assetRightsCsvPath": str(csv_path),
        "assetRightsReadinessPercent": manifest["summary"]["readinessPercent"],
        "assetRightsBlockerCount": manifest["summary"]["blockerCount"],
        "assetRightsWarningCount": manifest["summary"]["warningCount"],
    }


__all__ = [
    "EXPORT_ASSET_RIGHTS_JSON_NAME",
    "EXPORT_ASSET_RIGHTS_REPORT_NAME",
    "EXPORT_ASSET_RIGHTS_CSV_NAME",
    "build_asset_usage_index",
    "build_export_asset_rights_manifest",
    "build_export_asset_rights_report",
    "build_export_asset_rights_csv",
    "write_export_asset_rights_files",
]
