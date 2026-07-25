from __future__ import annotations

import unittest

from native_runtime.runtime_text_input import (
    append_text_input_value,
    collect_runtime_text_variable_ids,
    interpolate_runtime_text,
    normalize_text_input_block,
    sanitize_text_input_value,
)


class NativeRuntimeTextInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.variables = {
            "player_name": {"id": "player_name", "type": "string", "defaultValue": "旅人"},
            "score": {"id": "score", "type": "number", "defaultValue": 0},
            "flag": {"id": "flag", "type": "boolean", "defaultValue": False},
        }

    def test_normalization_interpolation_and_token_collection(self) -> None:
        config = normalize_text_input_block({"prompt": " ", "maxLength": 999, "allowEmpty": True})
        self.assertEqual(config["prompt"], "请输入内容")
        self.assertEqual(config["maxLength"], 200)
        self.assertTrue(config["allowEmpty"])
        self.assertEqual(
            collect_runtime_text_variable_ids("你好 {{ player_name }}", ["{{score}}", "{{player_name}}"]),
            ["player_name", "score"],
        )
        self.assertEqual(
            interpolate_runtime_text(
                "{{player_name}} 得分 {{score}}，{{unknown}}",
                {"player_name": "小夏", "score": 12},
                self.variables,
            ),
            "小夏 得分 12，{{unknown}}",
        )
        self.assertEqual(interpolate_runtime_text("欢迎 {{player_name}}", {}, self.variables), "欢迎 旅人")
        self.assertEqual(
            interpolate_runtime_text("A{{missing}}B", {}, self.variables, keep_unknown=False),
            "AB",
        )

    def test_text_and_number_inputs_are_safely_sanitized(self) -> None:
        text_result = sanitize_text_input_value(
            "  小夏  ",
            {"maxLength": 8},
            self.variables["player_name"],
        )
        number_result = sanitize_text_input_value(
            " 12.5 ",
            {"maxLength": 8},
            self.variables["score"],
        )
        self.assertTrue(text_result["ok"])
        self.assertEqual(text_result["value"], "小夏")
        self.assertTrue(number_result["ok"])
        self.assertEqual(number_result["value"], 12.5)
        self.assertFalse(
            sanitize_text_input_value("十二", {"maxLength": 8}, self.variables["score"])["ok"]
        )
        self.assertFalse(
            sanitize_text_input_value("abcdef", {"maxLength": 4}, self.variables["player_name"])["ok"]
        )
        self.assertFalse(
            sanitize_text_input_value("yes", {"maxLength": 8}, self.variables["flag"])["ok"]
        )
        self.assertEqual(append_text_input_value("ab", "中文", 3), "ab中")


if __name__ == "__main__":
    unittest.main()
