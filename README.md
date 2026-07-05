<p align="center">
  <img src="docs/github/canvasia-engine-hero.png" alt="Canvasia Engine hero" width="100%" />
</p>

<h1 align="center">Canvasia Engine</h1>

<p align="center">
  A creator-friendly visual novel / galgame engine prototype.<br />
  Build playable stories with assets, dialogue, buttons, previews, and export tools instead of code.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-source--available%20preview-3fb7ff?style=for-the-badge" alt="Status: Source-Available Preview" />
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-0e1628?style=for-the-badge" alt="Platforms" />
  <img src="https://img.shields.io/badge/tests-smoke%20%2B%20playwright-1fc98b?style=for-the-badge" alt="Tests" />
  <img src="https://img.shields.io/badge/license-Creator%20License%201.0-f5c451?style=for-the-badge" alt="Creator License 1.0" />
</p>

<p align="center">
  <strong>Language</strong>:
  <a href="README.zh-CN.md">简体中文</a> ·
  English ·
  <a href="README.ja-JP.md">日本語</a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#core-features">Core Features</a> ·
  <a href="#feature-status">Feature Status</a> ·
  <a href="#exports">Exports</a> ·
  <a href="#project-site-and-share-kit">Share Kit</a> ·
  <a href="#testing">Testing</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## Project Positioning

Canvasia Engine is currently a source-available preview for visual novel and galgame creators.

It is best suited for:

- trying small visual novel prototypes
- testing editor and export workflows
- building small creator projects
- collecting feedback before a stable commercial release

The project already includes a visual editor, export pipeline, native runtime preview, project recovery tools, and automated smoke tests. It is still published as **Preview / Early Access** because signing, notarization, installers, and long manual QA still need more release hardening.

## Core Features

- Visual story editor with scenes, cards, dialogue, narration, choices, variables, and conditional branches
- Project center with playable Demo projects, blank projects, beginner mode, advanced mode, and a six-stage creator workflow guide from project setup to Release Candidate export
- Context-aware Command Palette with Cmd/Ctrl+K quick actions for project setup, navigation, recommended next steps, recent commands, story card insertion, a previewed first-playable-scene template, themes, tutorial access, and export flow
- Production-ready scene recipes for OP hooks, daily dialogue rhythm, affection choices, mystery clues, relationship reveals, branch merges, climax direction, ED / credits, BGM range scoping, and variable-backed branch consequences
- Scene mood recipes that insert editable camera, filter, particle, pause, flash, shake, BGM, and fade cards for common VN beats such as confession focus, mystery pressure, rainy memory, climax impact, and quiet endings
- Plain-text and Ren'Py-style script import that previews `Character: line`, quoted dialogue, narration, choices with `[affection +1; flag=true]` consequences, `scene`, `show`, `hide`, `show ... scale / x / y / opacity / layer / flip`, per-line `speed slow / normal / fast / instant`, standalone variable cues such as `set route = common` and `add affection +1`, `if affection >= 2 -> good else -> normal`, `play / stop music`, `play sound`, `play video`, `wait / pause`, `shake`, `flash`, `zoom`, `pan`, `filter`, `blur`, `particle`, `credits`, `voice`, and `jump` cues as editable story / staging / text-speed / variable / condition / audio / video / timing / camera / atmosphere / route cards
- Asset management for backgrounds, character sprites, CGs, BGM, SFX, voice, fonts, UI assets, Live2D files, 3D models, and 3D scenes, with editable license / source / credit metadata, asset footprint radar reports for package-size risk, dependency reports that show where each asset is used, rights / credits sheets for commercial-use, placeholder, and AI provenance checks, plus one-click Staff / Credits draft generation from registered asset credits
- Multi-language project settings for default language and player-selectable languages
- Localized runtime text for scene names, chapter names, dialogue, choices, and character names, with safe fallback when a translation is missing
- Localization coverage checks with Markdown / CSV exports and safe CSV re-import for character, chapter, scene, and story-card translations
- Canvasia Assistant with local template mode and optional creator-provided OpenAI, DeepSeek, Qwen, Kimi, Zhipu GLM, or compatible API providers
- Optional OpenAI Image asset generation for backgrounds, sprites, CGs, and UI materials, with style-hint presets, sprite-to-character expression binding, prompt/model validation, and local-only API key handling
- Formal save/load, quick save/load, system menu, text history, autoplay, skip-read, and voice replay
- Entry reachability route analysis for broken links, orphan scenes, unreachable scenes, branch depth, ending candidates, playable ending path previews, and exportable route QA checklists
- Scene pacing advisor for playable-scene rhythm, long text, flat presentation, fake choices, missing outro cues, and next-action guidance in production boards
- Full screenplay / production-script exports for proofreading, voice recording, translation handoff, archival review, and Ren'Py draft migration notes
- Ren'Py draft export that converts scenes, dialogue, narration, choices, basic background / sprite / BGM cues, waits, and jumps into a reviewable `.rpy` starter file with a migration review manifest for custom effects
- Director cue-sheet exports that turn each scene into story, visual, audio, route, and effect production beats
- Release Candidate manifests that bundle project inventory, deliverable status, release risks, unlockable-content readiness, and manual signoff checks for testers and public preview handoff
- Unlockable Content manifests with Markdown / CSV exports for CG gallery, music room, voice replay, character archive, location archive, narration archive, relationship archive, chapter replay, ending collection, and achievement coverage
- Custom game UI skins, UI Kit binding, nine-slice textures, button states, layout controls, and visual novel textbox design
- Extra galleries: CG replay, music room, character archive, location archive, narration archive, relationship archive, achievements, chapter replay, ending replay, and voice replay
- Advanced particle presets, project particle libraries, camera effects, screen filters, flashes, shakes, and fade transitions
- Live2D / 3D character and 3D scene asset import, plus native-runtime 3D inspection reports for glTF / GLB / VRM assets
- Web playable, desktop, and native Runtime exports with runtime preload manifests for smoother first-scene asset loading, plus editor desktop builds
- Automated checks: local CI precheck, backend smoke tests, Playwright browser smoke tests, action wiring scans, branch-aware preview regression with condition / fallback variable presets, release-control reports, Release Candidate manifests, production backlog queues, Runtime capability matrices with export acceptance checklists, scene production boards with pacing-aware one-click recipe suggestions, full screenplay exports, Ren'Py draft exports, director cue sheets, voice production sheets, choice consequence audits, variable influence audits, asset dependency audits, asset rights / credits audits, unlockable-content audits, BGM cue-sheet audits, character stage-direction audits, presentation timeline audits, tester handoff work orders, playtest feedback templates and feedback intake summaries, VN baseline quality audits, and package integrity verification

## Feature Status

| Area | Status | Notes |
| --- | --- | --- |
| Story and Branch Editing | Available | Visual cards, choices, jumps, variables, conditions, entry reachability route checks, scene production boards with pacing-aware recipe suggestions, full screenplay exports, Ren'Py draft exports, director cue sheets, voice production sheets, variable influence reports, scene graph inspection, and plain-text script-to-card import. |
| Asset Management | Available | Import, replace, delete, usage protection, editable license / source / credit metadata, asset footprint radar reports for package-size risk, dependency reports, rights / credits reports for commercial-use, placeholder, AI provenance checks, and Staff / Credits draft generation, file-size budget hints, and optional OpenAI Image generation with style presets, sprite expression binding, prompt, model, format, and returned-file validation. |
| Multi-language / i18n | Preview | Project language settings, localization coverage reports, safe CSV re-import for character, chapter, scene, and story-card translations, export metadata, Web Runtime language switching, native Runtime language switching, and fallback behavior. |
| Canvasia Assistant | Available | Local template mode plus optional creator-owned API keys for major compatible providers. |
| Project Safety Net | Available | Snapshots, restore, crash recovery, project doctor, repair queue, cross-module production backlog queues, release gates, release-control reports, Release Candidate manifests, and VN baseline quality checks for placeholder content, character sprites, backgrounds, BGM, choices, text density, and presentation polish. |
| Game UI Customization | Available | Project UI skins, button states, nine-slice images, layout tuning, and textbox styling. |
| Extras / Replay Systems | Available | CG, music, character, location, narration, relationship, achievement, chapter, ending, and voice replay systems, plus exportable Unlockable Content manifests that catch missing gallery files, voice replay gaps, character archive visuals, and unreachable endings. |
| Particles and Presentation | Available | Particle presets, custom particle settings, scene mood recipes, camera, filters, flashes, shakes, fades, and character presentation effects. |
| Live2D / 3D Assets | Preview | Live2D, 3D character models, and 3D scene assets can be imported; native Runtime exports 3D structure and risk reports. |
| Web / Desktop Exports | Preview | Web playable packages and desktop packages are available; signing and notarization depend on release notes. |
| Native Runtime | Preview | Covers the core playback path, settings, saves, history, autoplay, video fallback, 3D reports, first archive systems, and editor-side Runtime capability matrices with Web / native acceptance checklists. |
| Mobile Runtime | Experimental planning | Touch, audio policy, and layout adaptation are still being explored. |

## Screenshots

| Story Editor and Assistant | Preview and Export |
| --- | --- |
| ![Canvasia Engine story editor with assistant](docs/github/canvasia-screenshot-story-assistant.png) | ![Canvasia Engine preview and export screen](docs/github/canvasia-screenshot-preview-export.png) |
| Visual story cards, scene structure, Canvasia Assistant, idea vault, and insertable generated cards. | Preview, runtime settings, release checks, and multi-platform export entry points. |

## Project Site and Share Kit

- Landing page source: [`docs/index.html`](docs/index.html)
- Social preview image: [`docs/github/canvasia-social-preview.png`](docs/github/canvasia-social-preview.png)
- Exposure kit: [`docs/marketing/exposure-kit.md`](docs/marketing/exposure-kit.md)
- Expected GitHub Pages URL after enabling Pages from `/docs`: `https://tonyna-code.github.io/canvasia-engine/`

## Repository Layout

- [`run_editor.py`](run_editor.py): local editor server, project management, export pipeline, and packaging entry point
- [`editor_local_security.py`](editor_local_security.py): loopback-only API request guard helpers
- [`editor_snapshot_cache.py`](editor_snapshot_cache.py): reusable file-signature snapshot cache for read-heavy editor payloads
- [`export_package_guide.py`](export_package_guide.py): exported package playtest / acceptance guide builder
- [`export_localization_audit.py`](export_localization_audit.py): exported package localization coverage audit for multilingual releases
- [`export_quality_reports.py`](export_quality_reports.py): shared exported quality-report bundle orchestration
- [`export_release_readiness.py`](export_release_readiness.py): exported package release-readiness summary and tester handoff gate builder
- [`export_story_route_map.py`](export_story_route_map.py): exported package story route map, broken-link, and unreachable-scene report builder
- [`export_unlockable_manifest.py`](export_unlockable_manifest.py): export-side unlockable / gallery / replay coverage manifest builder
- [`export_runtime_preload.py`](export_runtime_preload.py): exported Runtime preload manifest and performance report builder
- [`renpy_export.py`](renpy_export.py): Ren'Py Starter Bundle builder for migration-friendly `.rpy` exports
- [`prototype_editor`](prototype_editor): visual editor frontend
- [`prototype_editor/modules`](prototype_editor/modules): frontend pure-logic modules for route analysis, story templates, editor helpers, assistant workflows, release checks, and other testable editor capabilities
- [`export_player_template`](export_player_template): exported Web Runtime template
- [`native_runtime`](native_runtime): native Runtime player and related desktop runtime logic
- [`template_project`](template_project): blank starter project template
- [`tests`](tests): automated smoke and regression tests
- [`docs/maintainer-guide.md`](docs/maintainer-guide.md): maintenance boundaries, safe extension pattern, and recommended checks

## Quick Start

The editor only requires Python 3 for the source-based path.

If this is your first time opening Canvasia, follow the short route below:

1. Launch the editor.
2. In Project Center, create a playable Demo project.
3. Click through preview once to confirm the first scene, character, BGM, and dialogue all run.
4. Replace the placeholder assets and lines with your own story.
5. If you prefer a completely clean workspace, create a blank project and use the starter kit when you are ready.

### One-click scripts

- macOS: double-click [`start_editor.command`](start_editor.command)
- Windows: double-click [`start_editor.cmd`](start_editor.cmd)
- Linux: run [`start_editor.sh`](start_editor.sh)

### Command line

macOS / Linux:

```bash
git clone https://github.com/TonyNa-code/canvasia-engine.git
cd canvasia-engine
python3 run_editor.py
```

Windows:

```bat
git clone https://github.com/TonyNa-code/canvasia-engine.git
cd canvasia-engine
py -3 run_editor.py
```

If the Windows `py` launcher is unavailable, try:

```bat
python run_editor.py
```

After launch, the editor opens in your browser on a local `127.0.0.1` address. The project files stay on your computer.

## Recommended First Project

For a first five-minute demo, start small:

- 1 background
- 1 character sprite
- 1 BGM track
- 10 to 20 lines of dialogue
- 1 choice
- 1 simple ending

Build one complete path first, then add branches, effects, UI skins, galleries, voice, and extra polish.
The playable Demo project gives you that skeleton immediately. If you start from a blank project instead, the starter kit can create the first character/background/BGM records and connect them to the first scene, so you do not have to wire every card by hand.

If your draft already lives in a document or notes app, paste a short section into the story page's script import panel. `Character: dialogue` or `character "dialogue"` becomes dialogue, plain lines become narration, consecutive `- choice` or `"choice":` lines become one choice card, lightweight cues such as `scene classroom with fade`, `show heroine smile at right with dissolve scale 118 x -8 y 3 opacity 90 layer 2 flip`, `speed fast`, `hide heroine with fade`, `play music school_theme fadein 1.2`, `play sound door_knock`, `play video opening_movie title "Opening" volume 80 from 0 to 18 cover`, `wait 0.8`, `pause 1200ms`, `shake heavy short`, `flash white soft short`, `zoom in medium center`, `filter memory soft`, `blur right strong`, `particle snow heavy fast`, `credits title "STAFF" duration 24`, and `voice yuina_001` become editable staging / text-speed / audio / video / timing / camera / atmosphere / voice-linked cards. `set route = common`, `add affection +1`, `jump ending`, choice targets like `- Go to the roof -> rooftop`, choice consequences like `- Hold her hand -> rooftop [affection +1; met=true]`, and conditions like `if affection >= 2 -> good_ending else -> normal_ending` become variable cards, route links, variable effects, and condition cards after preview.

## Multi-language Projects

Canvasia supports a first i18n workflow:

1. Finish the main story in your primary language.
2. Open project runtime settings and choose the default language.
3. Enable player-selectable languages such as `zh-CN`, `ja-JP`, or `en-US`.
4. Add translations for character names, scene names, chapter names, dialogue, narration, and choices.
5. Open the inspection center and export a localization coverage report or CSV if you want a translator-friendly checklist.
6. Fill the translation column in the CSV and import it back to write supported character, chapter, scene, and story-card translations into the project.
7. Export and switch language in the Web Runtime or native Runtime settings menu.

If a translation is missing, the runtime falls back to the default text instead of breaking the game.

## Exports

Open a project and go to the preview/export area to generate:

- Web playable package
- Ren'Py Starter Bundle package
- Windows desktop package
- macOS desktop package
- Linux desktop package
- Native Runtime package preview with standalone-app build scaffolding

The Web playable package is the easiest option for quick sharing. The native Runtime package is the route for testing a more app-like desktop playback flow.

The Ren'Py Starter Bundle exports a zip with `game/script.rpy`, `game/options.rpy`, copied assets under `game/assets/`, a migration manifest, review notes for custom Canvasia effects, a bundle quality report, and a local verifier script for labels, jumps, and referenced files.

Every playable export also includes `README_试玩验收先看这里.md`, `story_route_map.json`, `story_route_map.md`, `localization_audit.json`, `localization_audit.md`, `release_readiness_summary.json`, `release_readiness_summary.md`, `unlockable_content_manifest.json`, `unlockable_content_report.md`, `runtime_preload_manifest.json`, and `RUNTIME_PRELOAD_REPORT.md`. The README gives testers launch steps and acceptance checks; the story route map catches broken jumps and unreachable scenes; the localization audit flags missing translations in multilingual projects; the release-readiness files summarize whether the package is ready to hand to testers; the unlockable JSON / Markdown pair covers CG galleries, music rooms, voice replay, archive pages, achievements, chapter replay, and endings; the runtime preload files record first-scene and early-route assets prepared for smoother playback. Native Runtime packages now consume the same preload manifest, warming critical image and short-audio caches at startup while continuing non-critical preload work in small background steps.

## Release Packages

Preview editor builds are distributed through GitHub Releases when available:

- `macos.tar.gz`
- `windows.zip`
- `linux.tar.gz`

Unsigned preview builds may trigger macOS Gatekeeper, Windows SmartScreen, or antivirus warnings. Download only from the official repository release page and verify SHA-256 files when provided.

## Testing

Useful local checks:

```bash
python3 -m unittest tests.test_run_editor_smoke -v
python3 -m unittest tests.test_frontend_particle_effects_module -v
node --check prototype_editor/app.js
node --check export_player_template/player.js
node --check export_player_template/runtime_audio.js
```

Some browser or native-rendering checks may require additional local dependencies.

## License

This project uses the Creator License 1.0 included in [`LICENSE`](LICENSE). Games made with the engine may be commercialized, while redistribution or commercialization of modified engine copies is limited by the license terms.

## Contributing

Contributions are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), and [`SECURITY.md`](SECURITY.md) before opening issues or pull requests.
