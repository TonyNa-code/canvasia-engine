# Canvasia UI Kit Packages

Canvasia UI Kit packages move a finished visual-novel interface between projects without leaving its fonts or artwork behind. The editor exports one portable `.canvasia-ui-kit.json` file and imports it as a single transaction.

## Creator Workflow

1. Open **Project Settings > Finished Game UI Skin** and finish the skin and textbox design.
2. Choose **Export Complete UI Kit**. Canvasia collects only the font and UI assets referenced by the current settings.
3. In another project, choose **Import UI Kit** and review the replacement summary.
4. Confirm once. The editor imports the assets, gives them project-local IDs, applies the skin and textbox settings, and records one project-history entry.

The package preserves asset display names, tags, license, source URL, author, credit, AI provenance, commercial-use status, and attribution requirements. It does not include story content, characters, saves, unrelated project assets, or API keys.

## Safety And Recovery

- Format: `canvasia-ui-kit`
- Current version: `1`
- Maximum embedded assets: `12`
- Maximum decoded size per asset: `12 MB`
- Maximum decoded asset total: `32 MB`
- Maximum package file size in the editor: `48 MB`
- Maximum backend request size: `64 MB`

Every package carries a canonical SHA-256 checksum. The editor verifies that checksum, validates every binding and declared asset type, rejects mismatched filename extensions, and checks all limits before committing the final project configuration. A failed import restores the previous project and asset index and removes newly written files.

SHA-256 detects accidental damage and post-export modification; it is not an author signature and does not prove who created a package. Creators should still review the included rights metadata before publishing a game.

## Versioning Contract

The root `format` and integer `version` fields are mandatory. Importers must reject unknown formats, unsupported versions, unknown binding paths, unbound embedded files, missing referenced files, and role/type mismatches instead of guessing.

Version 1 supports these project bindings:

- project font
- title background and title logo
- main panel nine-slice artwork
- default, hover, pressed, and disabled button artwork
- save-slot and system-panel artwork
- global UI overlay
- visual-novel textbox panel artwork

The version 1 importer intentionally rejects unknown root, asset, binding, and rights fields. Adding even an optional schema field, changing a binding meaning, changing asset encoding, or changing the integrity algorithm therefore requires a new package version and an explicit migration path.

## Maintenance Checklist

When changing the package contract, update all of the following in one change:

- `prototype_editor/modules/ui_kit_package.js` for browser export, validation, and request shaping
- `editor_ui_kit.py` for backend binding and ID-rewrite policy
- `run_editor.py` for transactional filesystem and project persistence only
- `prototype_editor/modules/project_runtime_settings_panel.js` and `prototype_editor/app.js` for product actions
- frontend, pure backend, integration rollback, module guard, entrypoint, local verification, and CI coverage tests

Do not move binary encoding, checksumming, or package-schema logic into `app.js`, and do not teach native or Web game Runtimes to import creator packages. Runtimes consume the already-normalized project configuration and project-local assets.
