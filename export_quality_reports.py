from __future__ import annotations

from pathlib import Path

from export_localization_audit import write_export_localization_audit_files
from export_release_readiness import write_export_release_readiness_files
from export_story_route_map import write_export_story_route_map_files


def normalize_report_file_names(values: list[str] | None) -> list[str]:
    report_names: list[str] = []
    for value in values or []:
        report_name = str(value or "").strip()
        if report_name and report_name not in report_names:
            report_names.append(report_name)
    return report_names


def write_export_quality_report_bundle(
    target_dir: Path,
    *,
    bundle: dict,
    project: dict,
    manifest: dict,
    missing_assets: list[dict] | None = None,
    unlockable_manifest: dict | None = None,
    base_report_files: list[str] | None = None,
    extra_report_files: list[str] | None = None,
    platform_notes: list[str] | None = None,
) -> dict:
    story_route_map = write_export_story_route_map_files(target_dir, bundle)
    localization_audit = write_export_localization_audit_files(target_dir, bundle)
    report_files = normalize_report_file_names(
        [
            *(base_report_files or []),
            story_route_map["storyRouteMapReportName"],
            localization_audit["localizationAuditReportName"],
            *(extra_report_files or []),
        ]
    )
    release_readiness = write_export_release_readiness_files(
        target_dir,
        project=project,
        manifest=manifest,
        missing_assets=missing_assets,
        unlockable_manifest=unlockable_manifest,
        story_route_map=story_route_map["storyRouteMap"],
        localization_audit=localization_audit["localizationAudit"],
        report_files=report_files,
        platform_notes=platform_notes,
    )
    return {
        **story_route_map,
        **localization_audit,
        **release_readiness,
        "qualityReportFiles": report_files,
    }


__all__ = [
    "normalize_report_file_names",
    "write_export_quality_report_bundle",
]
