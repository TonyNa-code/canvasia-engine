# Canvasia Engine Preview Release Checklist

This checklist is for publishing a source-available Preview / Early Access build. It is not a promise that the engine is already a fully signed commercial stable release.

## Release Positioning

- Use `Preview`, `Early Access`, or `source-available preview` wording.
- Do not call the current build a fully stable commercial release yet.
- Make it clear that macOS / Windows signed installers are a later formal distribution step.
- Keep mobile Runtime support marked as experimental planning until Android / iOS packages are actually produced and tested.

## Must Pass Before GitHub Release

For the final short gate, also review [`RELEASE_P0.md`](RELEASE_P0.md).

- Run the full automated suite:

```bash
python3 -m unittest discover -s tests -v
```

- Run syntax checks:

```bash
python3 -m py_compile run_editor.py native_runtime/runtime_player.py native_runtime/build_native_runtime_app.py
node --check prototype_editor/app.js
node --check export_player_template/player.js
```

- Export a web build and confirm `export_manifest.json` exists.
- Export a native Runtime build and confirm `native-runtime-release-check.json` exists.
- Confirm the native Runtime release check has `summary.errors` equal to `0`.
- Confirm no local privacy-sensitive files are staged, especially certificates, keys, local project exports, or signing env files.
- Confirm GitHub Actions has passed both backend smoke and Playwright browser smoke tests on the release commit.
- Run `python3 tools/release/prepare_preview_release.py` and review the generated upload manifest before creating the GitHub Release.

## Native Runtime Preview Gate

Current Preview-ready criteria:

- Core story playback works.
- Native title screen can be inspected with `runtime_player.py --describe-title-screen .`.
- Save / load, quick save, player profile, and auto resume are present.
- System menu, text speed, volume, theme, and fullscreen settings are present.
- Archive/gallery/replay surfaces are functional enough for Preview.
- Crash logs are written to `~/.canvasia-engine/native-runtime-logs/`.
- Video cards can be inspected with `runtime_player.py --describe-video-bridge .`; in native Preview they use a system-player bridge rather than embedded decoding.
- `build_native_runtime_app.py --describe .` returns a packaging plan.
- PyInstaller packaging can produce a platform Preview zip on the target system.

Current known limitations:

- Video playback is not yet an embedded native Runtime decoder path.
- Mobile Runtime is not produced by PyInstaller.
- macOS unsigned apps can be blocked by Gatekeeper.
- Windows unsigned apps can trigger SmartScreen warnings.
- Linux packages are currently archive-based; AppImage/deb/rpm/Flatpak are future packaging layers.

## Platform Packaging Matrix

macOS:

- Run `打包原生Runtime应用.command` or `python3 build_native_runtime_app.py --mode onedir .` on macOS.
- Verify the generated `.app` starts locally.
- For Preview, unsigned zip is acceptable with a clear warning.
- For stable release, use Developer ID signing and notarization.

Windows:

- Run `build_native_runtime_app.bat` on Windows.
- Verify the generated `.exe` / onedir package on a clean Windows machine.
- For Preview, unsigned zip is acceptable with a SmartScreen warning note.
- For stable release, use code signing and preferably an installer.

Linux:

- Run `./build_native_runtime_app.sh` on Linux.
- Verify the generated executable directory on at least one mainstream distro.
- For Preview, archive distribution is acceptable.
- For stable release, consider AppImage, deb/rpm, or Flatpak.

Mobile:

- Do not advertise APK / IPA output yet.
- Short-term path: Web Runtime inside WebView for touch/audio testing.
- Mid-term path: Android-specific Runtime shell.
- Long-term path: independent Android / iOS Runtime sharing the same project format.

## Sample Project Gate

- The bundled sample project must not contain missing asset file errors.
- Warnings are allowed for Preview if they are explicitly called out.
- Current acceptable sample warning: SVG CG assets may be less reliable in native Runtime than PNG/JPG.
- Before stable release, convert SVG sample CG assets to PNG/JPG or teach the native Runtime to render SVG reliably.

## Suggested GitHub Release Body

```md
## Canvasia Engine Preview

This is a source-available Preview build for testing the editor, web export, and native Runtime packaging flow.

### Downloads

- Source code archive
- Editor package, if attached
- Native Runtime Preview package, if attached

### Important Notes

- macOS apps are currently unsigned / unnotarized unless stated otherwise, so Gatekeeper may warn.
- Windows apps are currently unsigned unless stated otherwise, so SmartScreen may warn.
- Linux packages are Preview archives and should be tested on the target distro.
- Mobile Runtime export is experimental planning and is not included as APK / IPA yet.

### Recommended First Test

Open the editor, create a blank project, add one chapter, run preview, export web build, then export native Runtime build.
```
