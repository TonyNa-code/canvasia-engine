from __future__ import annotations

import unittest

from native_runtime.runtime_i18n import (
    DEFAULT_PROJECT_LANGUAGE,
    build_runtime_language_fallback_chain,
    build_runtime_language_labels,
    get_localized_runtime_value,
    normalize_language_code,
    normalize_supported_languages,
)


class NativeRuntimeI18nTests(unittest.TestCase):
    def test_native_runtime_i18n_helpers_normalize_language_state(self) -> None:
        self.assertEqual(DEFAULT_PROJECT_LANGUAGE, "zh-CN")
        self.assertEqual(normalize_language_code("EN-us"), "en-US")
        self.assertEqual(normalize_language_code("ja-jp"), "ja-JP")
        self.assertEqual(normalize_language_code("../../secret", "en-US"), "en-US")
        self.assertEqual(
            normalize_supported_languages(["en-us", "ja-jp", "en-US"], "zh-CN"),
            ["zh-CN", "en-US", "ja-JP"],
        )

    def test_native_runtime_i18n_helpers_resolve_labels_and_text_fallback(self) -> None:
        labels = build_runtime_language_labels({"ko-KR": "한국어", "bad value": "Bad"})
        self.assertEqual(labels["en-US"], "English")
        self.assertEqual(labels["ko-KR"], "한국어")
        self.assertNotIn("bad value", labels)

        self.assertEqual(
            build_runtime_language_fallback_chain(
                language="ko-kr",
                fallback_language="ja-jp",
                default_language="en-us",
            ),
            ["ko-KR", "ja-JP", "en-US", "zh-CN"],
        )
        self.assertEqual(
            get_localized_runtime_value(
                {
                    "text": "原文",
                    "textTranslations": {
                        "ja-JP": "  こんにちは  ",
                        "en-US": "Hello",
                    },
                },
                "text",
                language="ko-KR",
                fallback_language="ja-JP",
                default_language="en-US",
            ),
            "こんにちは",
        )
        self.assertEqual(
            get_localized_runtime_value({"text": " Keep me "}, "text", language="en-US"),
            "Keep me",
        )


if __name__ == "__main__":
    unittest.main()
