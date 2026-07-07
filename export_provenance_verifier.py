from __future__ import annotations

import json
from pathlib import Path


def build_export_provenance_verifier_script(
    *,
    provenance_file_name: str,
    protection_profile: str,
    engine_signature: dict,
) -> str:
    expected_signature = json.dumps(engine_signature, ensure_ascii=False, sort_keys=True)
    return f'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

PROVENANCE_FILE_NAME = "{provenance_file_name}"
MANIFEST_FILE_NAME = "export_manifest.json"
EXPECTED_PROFILE = "{protection_profile}"
EXPECTED_SIGNATURE = {expected_signature}


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)
    return payload if isinstance(payload, dict) else {{}}


def compact_sha256(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_bundle(bundle_dir: Path) -> dict:
    provenance_path = bundle_dir / PROVENANCE_FILE_NAME
    manifest_path = bundle_dir / MANIFEST_FILE_NAME
    missing_files = []
    changed_files = []
    errors = []

    if not provenance_path.is_file():
        return {{
            "status": "fail",
            "checkedAt": now_iso(),
            "bundleDir": str(bundle_dir),
            "errors": [f"Missing {{PROVENANCE_FILE_NAME}}"],
            "summary": {{"missingCount": 1, "changedCount": 0, "sealMatched": False}},
        }}

    try:
        provenance = load_json(provenance_path)
    except Exception as error:
        return {{
            "status": "fail",
            "checkedAt": now_iso(),
            "bundleDir": str(bundle_dir),
            "errors": [f"Cannot read {{PROVENANCE_FILE_NAME}}: {{error}}"],
            "summary": {{"missingCount": 0, "changedCount": 0, "sealMatched": False}},
        }}

    manifest = {{}}
    if manifest_path.is_file():
        try:
            manifest = load_json(manifest_path)
        except Exception as error:
            errors.append(f"Cannot read {{MANIFEST_FILE_NAME}}: {{error}}")
    else:
        errors.append(f"Missing {{MANIFEST_FILE_NAME}}")

    for entry in provenance.get("files") or []:
        if not isinstance(entry, dict):
            continue
        relative_path = str(entry.get("path") or "").strip()
        if not relative_path:
            continue
        file_path = bundle_dir / relative_path
        expected_size = int(entry.get("sizeBytes") or 0)
        expected_sha256 = str(entry.get("sha256") or "")
        if not file_path.is_file():
            missing_files.append({{"path": relative_path, "expectedSha256": expected_sha256}})
            continue
        actual_size = file_path.stat().st_size
        actual_sha256 = sha256_file(file_path)
        if actual_size != expected_size or actual_sha256 != expected_sha256:
            changed_files.append(
                {{
                    "path": relative_path,
                    "expectedSizeBytes": expected_size,
                    "actualSizeBytes": actual_size,
                    "expectedSha256": expected_sha256,
                    "actualSha256": actual_sha256,
                }}
            )

    expected_seal = str((provenance.get("summary") or {{}}).get("seal") or "")
    seal_payload = {{
        "engine": manifest.get("engine") or {{}},
        "project": manifest.get("project") or {{}},
        "protection": manifest.get("protection") or {{}},
        "files": provenance.get("files") or [],
    }}
    actual_seal = compact_sha256(seal_payload)
    profile_matched = provenance.get("profile") == EXPECTED_PROFILE
    signature_matched = (provenance.get("engine") or {{}}).get("signature") == EXPECTED_SIGNATURE
    seal_matched = bool(expected_seal) and actual_seal == expected_seal
    status = "pass" if not errors and not missing_files and not changed_files and profile_matched and signature_matched and seal_matched else "fail"
    return {{
        "status": status,
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "profileMatched": profile_matched,
        "signatureMatched": signature_matched,
        "sealMatched": seal_matched,
        "expectedSeal": expected_seal,
        "actualSeal": actual_seal,
        "summary": {{
            "checkedFileCount": len(provenance.get("files") or []),
            "missingCount": len(missing_files),
            "changedCount": len(changed_files),
            "errorCount": len(errors),
        }},
        "missingFiles": missing_files[:50],
        "changedFiles": changed_files[:50],
        "errors": errors[:50],
    }}


def main() -> int:
    bundle_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    if bundle_dir.is_file():
        bundle_dir = bundle_dir.parent
    report = verify_bundle(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def build_export_provenance_shell_verifier(script_name: str) -> str:
    return "\n".join(
        [
            "#!/bin/sh",
            "set -eu",
            'cd "$(dirname "$0")"',
            "if command -v python3 >/dev/null 2>&1; then",
            f'  python3 "{script_name}" .',
            "else",
            f'  python "{script_name}" .',
            "fi",
            "",
        ]
    )


def build_export_provenance_windows_verifier(script_name: str) -> str:
    return "\n".join(
        [
            "@echo off",
            "setlocal",
            'cd /d "%~dp0"',
            f'py -3 "{script_name}" .',
            "if %ERRORLEVEL% EQU 0 exit /b 0",
            f'python "{script_name}" .',
            "exit /b %ERRORLEVEL%",
            "",
        ]
    )


def write_export_provenance_verifier_files(
    build_dir: Path,
    *,
    provenance_file_name: str,
    protection_profile: str,
    engine_signature: dict,
    script_name: str,
    mac_name: str,
    linux_name: str,
    windows_name: str,
) -> dict:
    script_path = build_dir / script_name
    mac_path = build_dir / mac_name
    linux_path = build_dir / linux_name
    windows_path = build_dir / windows_name
    script_path.write_text(
        build_export_provenance_verifier_script(
            provenance_file_name=provenance_file_name,
            protection_profile=protection_profile,
            engine_signature=engine_signature,
        ),
        encoding="utf-8",
    )
    mac_path.write_text(build_export_provenance_shell_verifier(script_path.name), encoding="utf-8")
    linux_path.write_text(build_export_provenance_shell_verifier(script_path.name), encoding="utf-8")
    windows_path.write_text(build_export_provenance_windows_verifier(script_path.name), encoding="utf-8")
    script_path.chmod(0o755)
    mac_path.chmod(0o755)
    linux_path.chmod(0o755)
    return {
        "provenanceVerifierName": script_path.name,
        "provenanceVerifierPath": str(script_path),
        "provenanceVerifierMacName": mac_path.name,
        "provenanceVerifierMacPath": str(mac_path),
        "provenanceVerifierLinuxName": linux_path.name,
        "provenanceVerifierLinuxPath": str(linux_path),
        "provenanceVerifierWindowsName": windows_path.name,
        "provenanceVerifierWindowsPath": str(windows_path),
        "paths": [script_path, mac_path, linux_path, windows_path],
    }
