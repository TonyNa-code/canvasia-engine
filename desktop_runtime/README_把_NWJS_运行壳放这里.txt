Canvasia Engine · NW.js 本地运行壳投放说明

如果你想在外网受限的环境里导出真正的原生桌面包，可以把 NW.js 运行壳手动放到这里。

当前支持这些运行壳：
- Windows：nwjs-v0.105.0-win-x64.zip
- macOS：nwjs-v0.105.0-osx-arm64.zip
- Linux：nwjs-v0.105.0-linux-x64.tar.gz

支持这几种放法：
1. 直接把压缩包放进 desktop_runtime/ 或对应平台子目录（windows / macos / linux）
2. 解压成目录后放进去
3. 或者用环境变量指定：CANVASIA_NWJS_RUNTIME_DIR_<PLATFORM> / CANVASIA_NWJS_RUNTIME_ARCHIVE_<PLATFORM>
   例如：CANVASIA_NWJS_RUNTIME_DIR_WINDOWS、CANVASIA_NWJS_RUNTIME_ARCHIVE_MACOS

编辑器下次导出桌面包时，会先找这里的本地运行壳，再尝试联网下载。
