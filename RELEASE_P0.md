# Canvasia Engine Preview P0 Release Gate

This page is the final go / no-go checklist before publishing a GitHub Preview release.

## Positioning

- Publish as `Preview`, `Early Access`, or `source-available preview`.
- Do not present this build as a fully signed commercial stable release.
- Make unsigned macOS / Windows behavior explicit in the release notes.
- Do not advertise Android APK or iOS IPA export yet.

## Must Pass

- `python3 -m unittest discover -s tests -v`
- `python3 -m py_compile run_editor.py native_runtime/runtime_player.py native_runtime/build_native_runtime_app.py`
- `node --check prototype_editor/app.js`
- `node --check export_player_template/player.js`
- `git diff --check`
- GitHub Actions `CI / verify` is green after push, including backend smoke and Playwright browser smoke tests.

## Privacy Gate

Before publishing, scan staged files and the full tracked tree for:

- Local absolute paths such as `/Users/...`
- Real personal names beyond the public maintainer alias
- Private keys, certificates, tokens, passwords, signing env files
- Local project exports, generated app bundles, large runtime caches
- Personal screenshots or temporary files

Recommended scan:

```bash
CANVASIA_PRIVACY_EXTRA_PATTERNS="old-real-name,old-username" python3 tools/release/prepare_preview_release.py
rg -n --hidden --glob '!.git/**' --glob '!exports/**' --glob '!projects/**' --glob '!.export_runtime_cache/**' --glob '!__pycache__/**' --glob '!*.pyc' "BEGIN [A-Z ]*PRIVATE KEY|ghp_|github_pat_|password\\s*[:=]|secret\\s*[:=]|api[_-]?key\\s*[:=]" .
find . -path './.git' -prune -o -path './exports' -prune -o -path './projects' -prune -o -path './.export_runtime_cache' -prune -o -type f -size +20M -print
```

Expected result: no real secrets or personal local files. Code identifiers such as `tokenize_*`, CSS classes, sample support emails, and story IDs may appear as false positives.

## Release Artifacts

Minimum acceptable Preview release:

- Source code archive from GitHub
- Clear README instructions for macOS / Windows / Linux source startup
- Optional editor package if generated and manually tested
- Optional native Runtime Preview package if generated and manually tested

If no signed installer is attached, say so clearly.

## Manual Smoke

Run at least once before calling the release ready:

- Start editor from source.
- Create a blank project.
- Add one chapter and one scene.
- Add a background, one line, and one choice.
- Preview the project.
- Export web build.
- Export native Runtime build.
- Open `native-runtime-release-check.json` and confirm `summary.errors` is `0`.
- Run `runtime_player.py --describe-title-screen .` inside a native export.
- Run `runtime_player.py --describe-video-bridge .` if the project has videos.

## Known Preview Limits To Disclose

- Native Runtime embedded video uses the optional PyAV/FFmpeg path and still requires target-device codec testing; the system-player bridge remains the compatibility fallback.
- Mobile Runtime export is planning / experimental only.
- macOS unsigned apps may be blocked by Gatekeeper.
- Windows unsigned apps may trigger SmartScreen.
- Linux packages are archive-based; AppImage / deb / rpm / Flatpak are future packaging layers.
