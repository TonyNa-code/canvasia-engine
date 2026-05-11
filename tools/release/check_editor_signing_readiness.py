#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import run_editor


def bool_label(value: bool) -> str:
    return "已就绪" if value else "未就绪"


def build_report() -> dict:
    config, config_path = run_editor.load_editor_distribution_config()
    mac_settings = run_editor.resolve_editor_signing_settings(config)
    win_compile = run_editor.resolve_windows_installer_compiler_settings(config)
    win_sign = run_editor.resolve_windows_signing_settings(config)

    mac_codesign = shutil.which("codesign") or ""
    mac_productsign = shutil.which("productsign") or ""
    mac_xcrun = shutil.which("xcrun") or ""

    windows_pfx_path = str(win_sign.get("pfxPath") or "").strip()
    windows_pfx_exists = bool(windows_pfx_path) and Path(windows_pfx_path).exists()
    windows_cert_configured = bool(
        win_sign.get("certificateSubject") or win_sign.get("certificateThumbprint") or windows_pfx_exists
    )

    mac_app_ready = bool(mac_settings.get("macAppIdentity")) and bool(mac_codesign)
    mac_installer_ready = bool(mac_settings.get("macInstallerIdentity")) and bool(mac_productsign)
    mac_notary_ready = bool(mac_settings.get("macNotaryProfile")) and bool(mac_xcrun)

    windows_compile_ready = bool(win_compile.get("canCompile"))
    windows_sign_ready = bool(win_sign.get("signToolPath")) and windows_cert_configured
    windows_timestamp_ready = bool(win_sign.get("timestampUrl"))

    report = {
        "distributionConfigPath": str(config_path),
        "productName": config.get("productName") or "Canvasia Engine Editor",
        "bundleIdentifier": config.get("bundleIdentifier") or "",
        "macOS": {
            "appIdentity": mac_settings.get("macAppIdentity") or "",
            "installerIdentity": mac_settings.get("macInstallerIdentity") or "",
            "notaryProfile": mac_settings.get("macNotaryProfile") or "",
            "codesignPath": mac_codesign,
            "productsignPath": mac_productsign,
            "xcrunPath": mac_xcrun,
            "appSigningReady": mac_app_ready,
            "installerSigningReady": mac_installer_ready,
            "notaryReady": mac_notary_ready,
        },
        "windows": {
            "compilerPath": win_compile.get("compilerPath") or "",
            "compilerRunnerPath": win_compile.get("runnerPath") or "",
            "compilerReady": windows_compile_ready,
            "signToolPath": win_sign.get("signToolPath") or "",
            "signToolRunnerPath": win_sign.get("signToolRunner") or "",
            "certificateSubject": win_sign.get("certificateSubject") or "",
            "certificateThumbprint": win_sign.get("certificateThumbprint") or "",
            "pfxPath": windows_pfx_path,
            "pfxExists": windows_pfx_exists,
            "timestampUrl": win_sign.get("timestampUrl") or "",
            "certificateConfigured": windows_cert_configured,
            "signingReady": windows_sign_ready,
            "timestampReady": windows_timestamp_ready,
        },
        "summary": {
            "macCommercialReady": mac_app_ready and mac_installer_ready,
            "macNotaryReady": mac_notary_ready,
            "windowsCommercialReady": windows_compile_ready and windows_sign_ready and windows_timestamp_ready,
        },
    }
    return report


def print_human_report(report: dict) -> None:
    print("Canvasia Engine 维护者签名准备检查")
    print("")
    print(f"发行配置：{report['distributionConfigPath']}")
    print(f"产品名：{report['productName']}")
    print(f"包标识：{report['bundleIdentifier']}")
    print("")
    print("[macOS]")
    print(f"- App 签名：{bool_label(report['macOS']['appSigningReady'])}")
    print(f"- Installer 签名：{bool_label(report['macOS']['installerSigningReady'])}")
    print(f"- 公证：{bool_label(report['macOS']['notaryReady'])}")
    print(f"- codesign：{report['macOS']['codesignPath'] or '未找到'}")
    print(f"- productsign：{report['macOS']['productsignPath'] or '未找到'}")
    print(f"- xcrun：{report['macOS']['xcrunPath'] or '未找到'}")
    print(f"- App Identity：{report['macOS']['appIdentity'] or '未配置'}")
    print(f"- Installer Identity：{report['macOS']['installerIdentity'] or '未配置'}")
    print(f"- Notary Profile：{report['macOS']['notaryProfile'] or '未配置'}")
    print("")
    print("[Windows]")
    print(f"- 安装器编译：{bool_label(report['windows']['compilerReady'])}")
    print(f"- 安装器签名：{bool_label(report['windows']['signingReady'])}")
    print(f"- 时间戳：{bool_label(report['windows']['timestampReady'])}")
    print(f"- ISCC：{report['windows']['compilerPath'] or '未找到'}")
    print(f"- ISCC 运行器：{report['windows']['compilerRunnerPath'] or '未配置'}")
    print(f"- signtool：{report['windows']['signToolPath'] or '未找到'}")
    print(f"- signtool 运行器：{report['windows']['signToolRunnerPath'] or '未配置'}")
    print(
        f"- 证书："
        f"{report['windows']['certificateSubject'] or report['windows']['certificateThumbprint'] or report['windows']['pfxPath'] or '未配置'}"
    )
    print(f"- PFX 文件存在：{bool_label(report['windows']['pfxExists'])}")
    print(f"- 时间戳地址：{report['windows']['timestampUrl'] or '未配置'}")
    print("")
    print("[总览]")
    print(f"- mac 签名链就绪：{bool_label(report['summary']['macCommercialReady'])}")
    print(f"- mac 公证就绪：{bool_label(report['summary']['macNotaryReady'])}")
    print(f"- Windows 安装器签名链就绪：{bool_label(report['summary']['windowsCommercialReady'])}")


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 Canvasia Engine 编辑器维护者签名与公证准备状态")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
