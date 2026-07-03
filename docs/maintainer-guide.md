# Canvasia Engine Maintainer Guide

This guide explains the current maintenance boundaries for contributors who want to extend the engine without turning the main editor server into a harder-to-change file.

## Core Boundaries

- `run_editor.py` remains the source editor entry point. It owns the local HTTP server, project mutation commands, export commands, and packaging commands.
- `run_editor.py` also owns final writes for localization imports through `/api/import-localization-patches`; keep filesystem mutation for translated character / chapter / scene / block data there, while the frontend module prepares import plans.
- `editor_local_security.py` owns loopback-only editor API checks. Keep Host, Origin, and Referer policy changes there instead of spreading request-safety rules through handlers.
- `editor_snapshot_cache.py` owns small immutable-snapshot cache behavior. Reuse `SnapshotCache` for expensive read-mostly payloads that can be invalidated by a file signature.
- `openai_asset_generation.py` owns image-generation API calls and returned-file validation.
- `prototype_editor/modules/` owns browser-side editor logic that can be tested without a browser DOM.
- `prototype_editor/modules/command_palette.js` owns Cmd/Ctrl+K command metadata, filtering, recommendations, recent-command helpers, and list rendering. Keep command definitions there and route execution through existing editor actions.
- `prototype_editor/modules/story_templates.js` owns reusable story template presets, block recipes, template summaries, and the story-page template panel order. Add or tune scene templates there, while `app.js` should only translate recipes into real scene blocks and render summaries into UI surfaces.
- `prototype_editor/modules/script_importer.js` owns plain-text script parsing for the story page. Keep line-format recognition, choice grouping, preview summaries, and import limits there; `app.js` should only connect parsed draft blocks to the selected scene and persistence flow.
- `prototype_editor/modules/route_analyzer.js` owns pure scene-route analysis: route extraction, entry reachability, shortest entry paths, route QA case generation, broken-link detection, orphan / unreachable / ending metrics, route depth, validation issue counts, and per-scene production readiness. Keep future branch simulation or route scoring there so dashboard, project doctor, release gates, and tests share one route model.
- `prototype_editor/modules/route_testing_report.js` owns route QA report serialization, Markdown tables, standalone Markdown export content, and CSV rows. Keep route report formatting there instead of adding more report-specific table logic to `app.js`.
- `prototype_editor/modules/preview_regression.js` owns automatic preview-regression seed selection, branch-choice targeting, and best-effort condition / fallback variable presets for route smoke tests. Keep future route-smoke prioritization there so `app.js` only runs the selected seeds through the editor preview runtime.
- `prototype_editor/modules/playtest_handoff_report.js` owns tester-facing playtest handoff exports and intake: route cases, regression smoke results, fix queues, Markdown work orders, feedback templates, feedback CSV parsing, intake summaries, and CSV rows. Keep tester handoff wording and table formats there so `app.js` only wires buttons, downloads, and local file selection.
- `prototype_editor/modules/choice_consequence_sheet.js` owns choice consequence analysis and export formatting: option target summaries, variable-effect summaries, fake-choice warnings, duplicate option checks, broken target checks, broken variable checks, Markdown, and CSV. Keep future choice-design QA there instead of scattering branch-consequence rules across route and inspection UI code.
- `prototype_editor/modules/variable_influence_sheet.js` owns variable influence analysis and export formatting: variable definitions, read/write locations, choice effects, condition reads, unknown references, type mismatch checks, range checks, Markdown, and CSV. Keep future flag / affection / route-variable QA there instead of scattering variable-audit logic across story editing and inspection UI code.
- `prototype_editor/modules/audio_cue_sheet.js` owns BGM cue-sheet analysis and export formatting: music range summaries, missing BGM asset checks, invalid range targets, takeover warnings, fade suggestions, Markdown, and CSV. Keep future audio scheduling checks there so `app.js` remains a thin inspection/export surface.
- `prototype_editor/modules/stage_direction_sheet.js` owns character stage-direction analysis and export formatting: background coverage, character show / hide continuity, speaker auto-placement warnings, expression and visual asset readiness, Markdown, and CSV. Keep future staging continuity checks there instead of adding more production-audit logic to `app.js`.
- `prototype_editor/modules/presentation_timeline.js` owns release-facing presentation timeline analysis and export formatting: scene rhythm, text duration estimates, visual / audio anchors, hard-cut warnings, long static text runs, Markdown, and CSV. Keep future production-timeline rules there so inspection UI remains a thin shell.
- `prototype_editor/modules/localization_coverage.js` owns editor-side i18n coverage and translator handoff logic: supported-language discovery, chapter / scene / character / dialogue / narration / choice text coverage, missing translation checks, same-as-source warnings, Markdown / CSV export, CSV parsing, and safe import-plan generation. Keep future translation QA there so runtime fallback logic and inspection UI stay separate.
- `native_runtime/runtime_player.py` owns native playback, native release checks, and runtime reports.

## Safe Extension Pattern

When adding a new backend capability:

1. Put reusable pure logic in a focused module when it can stand alone.
2. Keep `run_editor.py` as the command/API integration layer.
3. Add a small unit test for the pure module.
4. Add an integration or smoke test when the feature touches project files, exports, or runtime behavior.
5. Add new Python modules to `tools/ci/local_verify.py` so `--profile syntax` catches syntax errors before release.

## Project Data Cache

The editor frequently asks `/api/project-data` for the full current project bundle. The bundle cache is intentionally conservative:

- It watches project metadata, assets, characters, variables, chapters, history, session state, and referenced asset files.
- It returns deep copies so UI handlers and tests cannot mutate the stored cache by accident.
- It refreshes automatically when watched file size or modified time changes.

If a future feature writes project files outside the existing helpers, make sure the watched signature includes the new file or call `clear_project_bundle_cache()` after the write.

## API Safety

The source editor is meant to run on loopback addresses such as `127.0.0.1` and `localhost`. API handlers should continue to reject non-local Host, Origin, or Referer values so another website cannot drive local project mutations.

When adding a new `/api/*` route:

- Keep it behind the shared `EditorRequestHandler` request guard.
- Return JSON errors for user-facing failures.
- Avoid writing outside the active project or approved export/cache directories.

## Recommended Checks

Use these checks before larger changes:

```bash
python3 tools/ci/local_verify.py --profile syntax
python3 -m unittest tests.test_editor_infrastructure tests.test_local_verify_tool -v
python3 -m unittest tests.test_run_editor_smoke -v
python3 -m unittest tests.test_release_public_surface -v
```

For frontend-only changes, also run the relevant `tests/test_frontend_*` module and `node --check` on the touched script.
