from __future__ import annotations

from pathlib import Path

from export_choice_consequence_sheet import write_export_choice_consequence_files
from export_localization_audit import write_export_localization_audit_files
from export_performance_budget import (
    EXPORT_PERFORMANCE_BUDGET_CSV_NAME,
    EXPORT_PERFORMANCE_BUDGET_JSON_NAME,
    EXPORT_PERFORMANCE_BUDGET_REPORT_NAME,
    write_export_performance_budget_files,
)
from export_release_fix_order import (
    EXPORT_RELEASE_FIX_ORDER_CSV_NAME,
    EXPORT_RELEASE_FIX_ORDER_JSON_NAME,
    EXPORT_RELEASE_FIX_ORDER_REPORT_NAME,
    write_export_release_fix_order_files,
)
from export_release_readiness import write_export_release_readiness_files
from export_route_playtest_workbook import write_export_route_playtest_workbook_files
from export_runtime_capability import write_export_runtime_capability_files
from export_story_route_map import write_export_story_route_map_files
from export_variable_influence_sheet import write_export_variable_influence_files


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
    assets_doc: dict | None = None,
    project: dict,
    manifest: dict,
    missing_assets: list[dict] | None = None,
    unlockable_manifest: dict | None = None,
    base_report_files: list[str] | None = None,
    extra_report_files: list[str] | None = None,
    platform_notes: list[str] | None = None,
) -> dict:
    story_route_map = write_export_story_route_map_files(target_dir, bundle)
    route_playtest = write_export_route_playtest_workbook_files(target_dir, bundle=bundle)
    choice_consequence = write_export_choice_consequence_files(target_dir, bundle=bundle)
    variable_influence = write_export_variable_influence_files(target_dir, bundle=bundle)
    runtime_capability = write_export_runtime_capability_files(target_dir, bundle=bundle)
    localization_audit = write_export_localization_audit_files(target_dir, bundle)
    performance_budget = write_export_performance_budget_files(target_dir, bundle=bundle, assets_doc=assets_doc)
    report_files = normalize_report_file_names(
        [
            *(base_report_files or []),
            story_route_map["storyRouteMapReportName"],
            route_playtest["routePlaytestWorkbookReportName"],
            route_playtest["routePlaytestWorkbookName"],
            route_playtest["routePlaytestWorkbookCsvName"],
            choice_consequence["choiceConsequenceReportName"],
            choice_consequence["choiceConsequenceName"],
            choice_consequence["choiceConsequenceCsvName"],
            variable_influence["variableInfluenceReportName"],
            variable_influence["variableInfluenceName"],
            variable_influence["variableInfluenceCsvName"],
            runtime_capability["runtimeCapabilityReportName"],
            runtime_capability["runtimeCapabilityMatrixName"],
            runtime_capability["runtimeCapabilityCsvName"],
            localization_audit["localizationAuditReportName"],
            performance_budget["exportPerformanceBudgetReportName"],
            performance_budget["exportPerformanceBudgetName"],
            performance_budget["exportPerformanceBudgetCsvName"],
            EXPORT_RELEASE_FIX_ORDER_REPORT_NAME,
            EXPORT_RELEASE_FIX_ORDER_JSON_NAME,
            EXPORT_RELEASE_FIX_ORDER_CSV_NAME,
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
        runtime_capability_matrix=runtime_capability["runtimeCapabilityMatrix"],
        performance_budget_report=performance_budget["exportPerformanceBudget"],
        report_files=report_files,
        platform_notes=platform_notes,
    )
    release_fix_order = write_export_release_fix_order_files(
        target_dir,
        project=project,
        release_readiness_summary=release_readiness["releaseReadinessSummary"],
        route_playtest_workbook=route_playtest["routePlaytestWorkbook"],
        choice_consequence_sheet=choice_consequence["choiceConsequenceSheet"],
        variable_influence_sheet=variable_influence["variableInfluenceSheet"],
        runtime_capability_matrix=runtime_capability["runtimeCapabilityMatrix"],
        localization_audit=localization_audit["localizationAudit"],
        performance_budget_report=performance_budget["exportPerformanceBudget"],
        report_files=report_files,
    )
    return {
        **story_route_map,
        **route_playtest,
        **choice_consequence,
        **variable_influence,
        **runtime_capability,
        **localization_audit,
        **performance_budget,
        **release_readiness,
        **release_fix_order,
        "qualityReportFiles": report_files,
    }


__all__ = [
    "normalize_report_file_names",
    "write_export_quality_report_bundle",
]
