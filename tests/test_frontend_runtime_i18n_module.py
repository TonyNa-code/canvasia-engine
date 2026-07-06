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

            const labels = runtimeI18n.buildRuntimeLanguageLabels({{ "ko-KR": "한국어" }});
            assertEqual("built-in label", labels["en-US"], "English");
            assertEqual("custom label", labels["ko-KR"], "한국어");
            assertEqual("immutable labels", Object.isFrozen(labels), true);
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
