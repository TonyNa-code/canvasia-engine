from __future__ import annotations

import unittest

from editor_ui_kit import build_ui_kit_import_plan, normalize_ui_kit_bindings, prepare_ui_kit_import


class EditorUiKitTests(unittest.TestCase):
    def test_import_plan_rebinds_shared_assets_without_mutating_source(self) -> None:
        game_ui = {
            "panelFrameAssetId": "source_panel",
            "buttonFrameAssetId": "source_panel",
            "accentColor": "#55aaff",
        }
        dialog_box = {"panelAssetId": "source_panel", "textColor": "#ffffff"}

        plan = build_ui_kit_import_plan(
            game_ui_config=game_ui,
            dialog_box_config=dialog_box,
            bindings={
                "gameUiConfig.panelFrameAssetId": 0,
                "gameUiConfig.buttonFrameAssetId": 0,
                "dialogBoxConfig.panelAssetId": 0,
            },
            imported_assets=[{"id": "ui_imported_panel", "type": "ui"}],
        )

        self.assertEqual(plan["assetCount"], 1)
        self.assertEqual(plan["bindingCount"], 3)
        self.assertEqual(plan["gameUiConfig"]["panelFrameAssetId"], "ui_imported_panel")
        self.assertEqual(plan["gameUiConfig"]["buttonFrameAssetId"], "ui_imported_panel")
        self.assertEqual(plan["dialogBoxConfig"]["panelAssetId"], "ui_imported_panel")
        self.assertEqual(game_ui["panelFrameAssetId"], "source_panel")
        self.assertEqual(dialog_box["panelAssetId"], "source_panel")

    def test_import_plan_rejects_unbound_missing_and_wrong_type_assets(self) -> None:
        with self.assertRaisesRegex(ValueError, "没有绑定"):
            normalize_ui_kit_bindings({}, 1)

        with self.assertRaisesRegex(ValueError, "缺少 gameUiConfig.panelFrameAssetId"):
            build_ui_kit_import_plan(
                game_ui_config={"panelFrameAssetId": "source_panel"},
                dialog_box_config={},
                bindings={},
                imported_assets=[],
            )

        with self.assertRaisesRegex(ValueError, "不能绑定 background"):
            build_ui_kit_import_plan(
                game_ui_config={"panelFrameAssetId": "source_panel"},
                dialog_box_config={},
                bindings={"gameUiConfig.panelFrameAssetId": 0},
                imported_assets=[{"id": "bg_wrong", "type": "background"}],
            )

    def test_prepare_import_validates_files_before_storage_orchestration(self) -> None:
        payload = {
            "name": "Portable Skin",
            "gameUiConfig": {"panelFrameAssetId": "source_panel"},
            "dialogBoxConfig": {},
            "bindings": {"gameUiConfig.panelFrameAssetId": 0},
            "files": [{"name": "panel.png", "assetType": "ui", "dataBase64": "unused"}],
        }

        prepared = prepare_ui_kit_import(
            payload,
            decode_file=lambda item: (item["name"], b"png"),
            is_file_allowed=lambda asset_type, file_name: asset_type == "ui" and file_name.endswith(".png"),
            asset_type_labels={"ui": "界面"},
        )

        self.assertEqual(prepared["name"], "Portable Skin")
        self.assertEqual(prepared["totalAssetBytes"], 3)
        with self.assertRaisesRegex(ValueError, "不能作为界面类型"):
            prepare_ui_kit_import(
                {**payload, "files": [{**payload["files"][0], "name": "panel.mp3"}]},
                decode_file=lambda item: (item["name"], b"audio"),
                is_file_allowed=lambda asset_type, file_name: file_name.endswith(".png"),
                asset_type_labels={"ui": "界面"},
            )


if __name__ == "__main__":
    unittest.main()
