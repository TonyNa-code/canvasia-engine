from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
RUNTIME_I18N_PATH = ROOT_DIR / "export_player_template" / "runtime_i18n.js"


class FrontendRuntimeI18nModuleTests(unittest.TestCase):
    def test_runtime_i18n_helpers_normalize_languages_and_labels(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as runtimeI18n from {json.dumps(RUNTIME_I18N_PATH.as_uri())};

            function assertEqual(label, actual, expected) {{
              if (JSON.stringify(actual) !== JSON.stringify(expected)) {{
                throw new Error(`${{label}} mismatch: ${{JSON.stringify(actual)}} !== ${{JSON.stringify(expected)}}`);
              }}
            }}

            assertEqual("default language", runtimeI18n.DEFAULT_RUNTIME_LANGUAGE, "zh-CN");
            assertEqual("normalize en", runtimeI18n.normalizeLanguageCode("EN-us"), "en-US");
            assertEqual("normalize ja", runtimeI18n.normalizeLanguageCode("ja-jp"), "ja-JP");
            assertEqual("bad fallback", runtimeI18n.normalizeLanguageCode("../../secret", "en-US"), "en-US");
            assertEqual(
              "supported languages",
              runtimeI18n.normalizeSupportedLanguages(["en-us", "ja-jp", "en-US"], "zh-CN"),
              ["zh-CN", "en-US", "ja-JP"]
            );
            assertEqual(
              "fallback chain",
              runtimeI18n.buildRuntimeLanguageFallbackChain({{
                language: "ko-kr",
                fallbackLanguage: "ja-jp",
                defaultLanguage: "en-us",
              }}),
              ["ko-KR", "ja-JP", "en-US", "zh-CN"]
            );

            const labels = runtimeI18n.buildRuntimeLanguageLabels({{ "ko-KR": "한국어" }});
            assertEqual("built-in label", labels["en-US"], "English");
            assertEqual("custom label", labels["ko-KR"], "한국어");
            assertEqual("immutable labels", Object.isFrozen(labels), true);

            const localized = runtimeI18n.getLocalizedRuntimeValue(
              {{
                text: "原文",
                textTranslations: {{
                  "ja-JP": "  こんにちは  ",
                  "en-US": "Hello",
                }},
              }},
              "text",
              {{ language: "ko-KR", fallbackLanguage: "ja-JP", defaultLanguage: "en-US" }}
            );
            assertEqual("localized fallback text", localized, "こんにちは");
            const resolved = runtimeI18n.resolveLocalizedRuntimeValue(
              {{
                text: "原文",
                textTranslations: {{
                  "ja-JP": "  こんにちは  ",
                  "en-US": "Hello",
                }},
              }},
              "text",
              {{ language: "ko-KR", fallbackLanguage: "ja-JP", defaultLanguage: "en-US" }}
            );
            assertEqual("resolved value", resolved.value, "こんにちは");
            assertEqual("resolved requested language", resolved.requestedLanguage, "ko-KR");
            assertEqual("resolved used language", resolved.usedLanguage, "ja-JP");
            assertEqual("resolved fallback flag", resolved.fallbackUsed, true);
            assertEqual("resolved missing requested language", resolved.missingRequestedLanguage, true);
            assertEqual(
              "base text fallback",
              runtimeI18n.getLocalizedRuntimeValue({{ text: "Keep me" }}, "text", {{ language: "en-US" }}),
              "Keep me"
            );
            const report = runtimeI18n.buildRuntimeLocalizationFallbackReport([
              {{
                key: "text",
                sourceId: "line_1",
                requestedLanguage: "en-us",
                usedLanguage: "ja-jp",
                fallbackChain: ["en-us", "ja-jp", "zh-CN"],
                valuePreview: "こんにちは",
              }},
              {{
                key: "name",
                sourceId: "scene_1",
                requestedLanguage: "en-us",
                usedLanguage: "",
                valuePreview: "教室",
              }},
            ]);
            assertEqual("report count", report.count, 2);
            assertEqual("report requested language", report.byRequestedLanguage["en-US"], 2);
            assertEqual("report key text", report.byKey.text, 1);
            assertEqual("report latest source", report.latest.sourceId, "scene_1");
            assertEqual(
              "report summary",
              runtimeI18n.formatRuntimeLocalizationFallbackSummary(report.events),
              "2 处，已使用原文 · 最近 name:scene_1"
            );
            """
        )
        subprocess.run(
            ["node", "--input-type=module", "-e", script],
            check=True,
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
        )


if __name__ == "__main__":
    unittest.main()
