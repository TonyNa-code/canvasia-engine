from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_export_release_artifact_index(
    archive_path: Path,
    target_label: str,
    archive_checksum: dict,
    archive_verifiers: dict,
    release_notes: dict,
    internal_reports: list[dict],
) -> dict:
    artifact_json_path = archive_path.with_name(f"{archive_path.name}.release-artifacts.json")
    artifact_markdown_path = archive_path.with_name(f"{archive_path.name}.release-artifacts.md")
    upload_artifacts = [
        {
            "name": archive_path.name,
            "path": str(archive_path),
            "type": "archive",
            "description": "原生 Runtime 可分发压缩包。",
            "required": True,
            "sha256": archive_checksum.get("archiveSha256"),
            "sizeLabel": archive_checksum.get("archiveSizeLabel"),
        },
        {
            "name": archive_checksum.get("archiveChecksumName"),
            "path": archive_checksum.get("archiveChecksumPath"),
            "type": "checksum",
            "description": "压缩包 SHA-256 纯文本校验文件。",
            "required": True,
        },
        {
            "name": archive_checksum.get("archiveChecksumJsonName"),
            "path": archive_checksum.get("archiveChecksumJsonPath"),
            "type": "checksum_json",
            "description": "压缩包校验信息、大小和跨平台验证命令。",
            "required": True,
        },
        {
            "name": archive_verifiers.get("archiveVerifierMacName"),
            "path": archive_verifiers.get("archiveVerifierMacPath"),
            "type": "archive_verifier",
            "description": "macOS 一键校验下载压缩包 SHA-256。",
            "required": False,
        },
        {
            "name": archive_verifiers.get("archiveVerifierLinuxName"),
            "path": archive_verifiers.get("archiveVerifierLinuxPath"),
            "type": "archive_verifier",
            "description": "Linux 一键校验下载压缩包 SHA-256。",
            "required": False,
        },
        {
            "name": archive_verifiers.get("archiveVerifierWindowsName"),
            "path": archive_verifiers.get("archiveVerifierWindowsPath"),
            "type": "archive_verifier",
            "description": "Windows 一键校验下载压缩包 SHA-256。",
            "required": False,
        },
        {
            "name": release_notes.get("releaseNotesName"),
            "path": release_notes.get("releaseNotesPath"),
            "type": "release_notes_draft",
            "description": "可直接复制到 GitHub Release 正文的发布说明草稿。",
            "required": False,
        },
        {
            "name": artifact_markdown_path.name,
            "path": str(artifact_markdown_path),
            "type": "release_notes_helper",
            "description": "发布附件索引，可直接贴到 Release notes 或作为附件上传。",
            "required": False,
        },
        {
            "name": artifact_json_path.name,
            "path": str(artifact_json_path),
            "type": "artifact_manifest",
            "description": "机器可读发布附件索引。",
            "required": False,
        },
    ]
    payload = {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "targetLabel": target_label,
        "archive": {
            "name": archive_path.name,
            "path": str(archive_path),
            "sha256": archive_checksum.get("archiveSha256"),
            "sizeBytes": archive_checksum.get("archiveSizeBytes"),
            "sizeLabel": archive_checksum.get("archiveSizeLabel"),
            "checksum": archive_checksum.get("archiveChecksumName"),
            "checksumJson": archive_checksum.get("archiveChecksumJsonName"),
            "releaseNotesDraft": release_notes.get("releaseNotesName"),
            "verifiers": {
                "macos": archive_verifiers.get("archiveVerifierMacName"),
                "linux": archive_verifiers.get("archiveVerifierLinuxName"),
                "windows": archive_verifiers.get("archiveVerifierWindowsName"),
            },
        },
        "uploadArtifacts": upload_artifacts,
        "insideArchiveReports": internal_reports,
        "verifySteps": [
            "下载 zip，并把对应系统的一键校验脚本放在同一目录。",
            "运行 .verify.command / .verify.sh / .verify.bat 校验 zip 压缩包 SHA-256。",
            "如果不使用脚本，也可以用 .sha256 或 .checksum.json 里的命令手动校验。",
            "解压后运行 runtime_player.py --verify-file-integrity . 校验包内核心文件。",
            "再运行发布总控脚本或打开 native-runtime-release-control-report.md 复核发布状态。",
        ],
    }
    artifact_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 原生 Runtime 发布附件索引",
        "",
        f"- 类型：{target_label}",
        f"- 生成时间：{payload['generatedAt']}",
        f"- 压缩包：`{archive_path.name}`",
        f"- 大小：{archive_checksum.get('archiveSizeLabel') or '未知'}",
        f"- SHA-256：`{archive_checksum.get('archiveSha256') or '未生成'}`",
        "",
        "## 建议上传到 GitHub Release 的附件",
        "",
        "| 文件 | 必需 | 说明 |",
        "| --- | --- | --- |",
    ]
    for artifact in upload_artifacts:
        lines.append(
            f"| `{artifact.get('name') or ''}` | {'是' if artifact.get('required') else '否'} | {artifact.get('description') or ''} |"
        )
    lines.extend(["", "## 包内报告", "", "| 文件 | 说明 |", "| --- | --- |"])
    for report in internal_reports:
        lines.append(f"| `{report.get('name') or ''}` | {report.get('description') or ''} |")
    lines.extend(["", "## 下载者验证步骤", ""])
    for index, step in enumerate(payload["verifySteps"], start=1):
        lines.append(f"{index}. {step}")
    lines.extend(
        [
            "",
            "## Release Notes 摘要",
            "",
            "```md",
            f"- 下载 `{archive_path.name}` 后，先运行对应系统的 `.verify` 脚本或用 `{archive_checksum.get('archiveChecksumName')}` 校验压缩包 SHA-256。",
            "- 解压后运行 `python3 runtime_player.py --verify-file-integrity .` 校验包内核心文件。",
            "- 如需发布前复核，打开 `native-runtime-release-control-report.md`。",
            "```",
            "",
        ]
    )
    artifact_markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "releaseArtifactIndexName": artifact_markdown_path.name,
        "releaseArtifactIndexPath": str(artifact_markdown_path),
        "releaseArtifactIndexJsonName": artifact_json_path.name,
        "releaseArtifactIndexJsonPath": str(artifact_json_path),
        "releaseArtifactUploadCount": len(upload_artifacts),
    }
