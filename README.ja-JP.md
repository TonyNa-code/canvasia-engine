<p align="center">
  <img src="docs/github/canvasia-engine-hero.png" alt="Canvasia Engine hero" width="100%" />
</p>

<h1 align="center">Canvasia Engine</h1>

<p align="center">
  ビジュアルノベル / Galgame 制作者向けのビジュアル制作エンジン・プロトタイプです。<br />
  素材を追加し、台詞を書き、ボタンで確認しながら、コードを書かずにプレイ可能な作品を作ることを目指しています。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-source--available%20preview-3fb7ff?style=for-the-badge" alt="Status: Source-Available Preview" />
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-0e1628?style=for-the-badge" alt="Platforms" />
  <img src="https://img.shields.io/badge/tests-smoke%20%2B%20playwright-1fc98b?style=for-the-badge" alt="Tests" />
  <img src="https://img.shields.io/badge/license-Creator%20License%201.0-f5c451?style=for-the-badge" alt="Creator License 1.0" />
</p>

<p align="center">
  <strong>言語</strong>：
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.md">English</a> ·
  日本語
</p>

<p align="center">
  <a href="#クイックスタート">クイックスタート</a> ·
  <a href="#主な機能">主な機能</a> ·
  <a href="#機能ステータス">機能ステータス</a> ·
  <a href="#書き出し">書き出し</a> ·
  <a href="#project-site-and-share-kit">Share Kit</a> ·
  <a href="#テスト">テスト</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## プロジェクトの位置づけ

Canvasia Engine は、ビジュアルノベル / Galgame 制作者のための source-available preview 版です。

現在は次の用途に向いています。

- 小規模なビジュアルノベルの試作
- エディタと書き出しフローの検証
- 個人制作や同人制作の初期プロトタイプ
- 安定版リリース前の機能体験とフィードバック

ビジュアルエディタ、書き出しパイプライン、ネイティブ Runtime preview、プロジェクト復旧機能、自動 smoke test はすでに含まれています。署名、公証、インストーラー、長時間の手動 QA はまだ強化中のため、現時点では **Preview / Early Access** として公開しています。

## 主な機能

- シーン、カード、台詞、ナレーション、選択肢、変数、条件分岐を扱えるビジュアルストーリーエディタ
- プレイ可能な Demo プロジェクト、空白プロジェクト、新人向けモード、高度編集モードを備えたプロジェクトセンター
- 文脈対応の Command Palette で、Cmd/Ctrl+K からプロジェクト開始、画面移動、次のおすすめ操作、最近使ったコマンド、ストーリーカード挿入、内容を確認できる最初のプレイ可能シーンテンプレート、テーマ切替、チュートリアル、書き出し入口をすばやく検索
- OP 導入、日常会話、好感度選択肢、ミステリー手がかり、関係性の開示、分岐合流、クライマックス演出、ED / credits、BGM 範囲指定、変数つき分岐をまとめて挿入できる制作向けシーンレシピ
- 通常の台本テキストをプレビューし、`キャラクター: 台詞`、ナレーション行、連続した選択肢行、`wait 0.8` / `pause 1200ms` のようなテンポ調整キューを編集可能なストーリーカードへ変換
- 背景、立ち絵、CG、BGM、効果音、ボイス、フォント、UI 素材、Live2D、3D モデル、3D シーン素材の管理。パッケージ容量リスクを確認できる asset footprint radar / CSV と、初回ロード圧を確認できる Runtime preload budget / CSV も含みます。
- プロジェクトのデフォルト言語と、プレイヤーが切り替えられる言語設定
- シーン名、章名、台詞、選択肢、キャラクター名の翻訳テキストを Runtime 側で読み取り、未翻訳部分は安全にフォールバック
- 未翻訳や原文コピーの疑いがある項目を確認できる多言語カバレッジレポート、CSV 書き出し、安全な CSV 再インポート
- Canvasia Assistant：ローカルテンプレートモードと、制作者自身の OpenAI、DeepSeek、Qwen、Kimi、Zhipu GLM、互換 API プロバイダーに対応
- OpenAI Image を利用した背景、立ち絵、CG、UI 素材生成の任意機能。画風プリセット、立ち絵のキャラクター表情への紐付け、プロンプト、モデル名、形式、返却ファイルの検証とローカルのみの API Key 利用に対応
- 通常セーブ / ロード、クイックセーブ / ロード、システムメニュー、テキスト履歴、自動再生、既読スキップ、ボイス回想
- 入口からの到達可能性にもとづくルート分析。壊れたリンク、孤立シーン、入口から到達できないシーン、分岐深度、エンディング候補、到達可能なエンディング経路プレビュー、エクスポート可能なルート QA チェックリスト、公開前ルート試遊ワークブックを確認可能
- Scene pacing advisor により、試遊シーンのリズム、長文、平坦な演出、実質的な結果を持たない選択肢、収束不足を確認し、scene production board で次の作業を提示
- Ren'Py draft export により、シーン、台詞、ナレーション、選択肢、基本的な背景 / 立ち絵 / BGM、待機、ジャンプを `.rpy` の下書きへ変換し、手作業で確認すべきカスタム演出を migration notes として出力
- ゲーム UI スキン、UI Kit 素材バインド、9-slice テクスチャ、ボタン状態、レイアウト調整、ビジュアルノベル用テキストボックス設計
- CG 回想、音楽鑑賞、キャラクター図鑑、場所図鑑、ナレーション図鑑、関係図鑑、実績、章回想、エンディング回想、ボイス回想。CG、BGM、ボイス、図鑑、章、エンディング、実績の抜けを確認できる Unlockable Content manifest / CSV も出力可能
- 高度なパーティクルプリセット、プロジェクト単位のパーティクルライブラリ、カメラ演出、フィルター、フラッシュ、画面揺れ、フェード
- Live2D / 3D キャラクターと 3D シーン素材のインポート、ネイティブ Runtime での glTF / GLB / VRM 構造レポート
- Web 試遊パッケージ、デスクトップ書き出し、エディタデスクトップビルド、ネイティブ Runtime preview パッケージ。Web / desktop / native Runtime は preload manifest により、最初のシーンと序盤ルートの素材を優先的に準備し、エディタ側でも事前に startup-pressure report を確認できます。
- ローカル CI precheck、backend smoke、Playwright browser smoke、ボタン配線チェック、Ren'Py draft export test、条件 / fallback 変数プリセット付き分岐対応 preview regression、route playtest workbook、first-screen loading risks と route blockers も修正順に含める release-control report、startup-loading tasks も含む production backlog queue、Runtime capability matrix と export acceptance checklist、Runtime preload budget audit、pacing-aware one-click recipe suggestion 付き scene production board、voice production sheet、choice consequence audit、variable influence audit、asset dependency audit、asset footprint audit、unlockable-content audit、BGM cue sheet audit、character stage-direction audit、presentation timeline audit、テスター引き継ぎワークオーダー、プレイテストフィードバックテンプレートと取り込みサマリー、VN baseline quality audit、ファイル整合性検証

## 機能ステータス

| 領域 | 状態 | 説明 |
| --- | --- | --- |
| ストーリー / 分岐編集 | Available | カード、選択肢、ジャンプ、変数、条件分岐、入口到達可能性チェック、リズム分析に連動した配方提案つきシーン制作ボード、フル台本、Ren'Py draft export、ボイス制作シート、シーングラフ確認、台本テキストからカードへのインポートに対応。 |
| 素材管理 | Available | インポート、置き換え、削除、使用中保護、依存関係レポート、asset footprint radar、容量予算ヒント、画風プリセット / 立ち絵表情紐付け / プロンプト / モデル / 形式検証付きの任意 OpenAI Image 生成に対応。 |
| 多言語 / i18n | Preview | プロジェクト言語設定、多言語カバレッジレポート、キャラクター / 章 / シーン / ストーリーカード翻訳の安全な CSV 再インポート、書き出しメタデータ、Web Runtime 言語切替、ネイティブ Runtime 言語切替、フォールバック動作に対応。 |
| Canvasia Assistant | Available | ローカルテンプレートと、制作者自身の API Key を使う主要互換プロバイダーに対応。 |
| プロジェクト安全網 | Available | スナップショット、復元、クラッシュ復旧、プロジェクト Doctor、修復キュー、公開前チェック、release-control report、プレースホルダー、立ち絵、背景、BGM、選択肢、テキスト密度、演出の基礎品質チェック。 |
| ゲーム UI カスタマイズ | Available | UI スキン、ボタン状態、9-slice 画像、レイアウト調整、テキストボックス設計。 |
| EXTRA / 回想システム | Available | CG、音楽、キャラクター、場所、ナレーション、関係、実績、章、エンディング、ボイス回想。Unlockable Content manifest でギャラリー素材不足、ボイス回想不足、キャラクター図鑑素材不足、到達不能エンディングも確認可能。 |
| パーティクル / 演出 | Available | パーティクル、カメラ、フィルター、フラッシュ、画面揺れ、フェード、キャラクター演出。 |
| Live2D / 3D 素材 | Preview | Live2D、3D キャラクター、3D シーン素材をインポート可能。ネイティブ Runtime は 3D 構造とリスクレポートを出力。 |
| Web / Desktop 書き出し | Preview | Web 試遊パッケージとデスクトップパッケージに対応。署名と公証は Release notes に従います。 |
| ネイティブ Runtime | Preview | コア再生、設定、セーブ、履歴、自動再生、動画フォールバック、3D レポート、初期図鑑システム、Web / native Runtime coverage checks をカバー。 |
| Mobile Runtime | Experimental planning | タッチ操作、音声ポリシー、レイアウト適応を検証中。 |

## スクリーンショット

| ストーリーエディタと Assistant | プレビューと書き出し |
| --- | --- |
| ![Canvasia Engine story editor with assistant](docs/github/canvasia-screenshot-story-assistant.png) | ![Canvasia Engine preview and export screen](docs/github/canvasia-screenshot-preview-export.png) |
| ストーリーカード、シーン構造、Canvasia Assistant、アイデア保管庫、挿入可能な生成カード。 | プレビュー、Runtime 設定、公開前チェック、マルチプラットフォーム書き出し入口。 |

## Project Site and Share Kit

- Landing page source: [`docs/index.html`](docs/index.html)
- Social preview image: [`docs/github/canvasia-social-preview.png`](docs/github/canvasia-social-preview.png)
- Exposure kit: [`docs/marketing/exposure-kit.md`](docs/marketing/exposure-kit.md)
- Expected GitHub Pages URL after enabling Pages from `/docs`: `https://tonyna-code.github.io/canvasia-engine/`

## リポジトリ構成

- [`run_editor.py`](run_editor.py): ローカルエディタサーバー、プロジェクト管理、書き出し、パッケージング入口
- [`editor_static_cache.py`](editor_static_cache.py): ローカルエディタ静的ファイルの ETag / 304 revalidation helper
- [`export_package_guide.py`](export_package_guide.py): 書き出しパッケージ向け playtest / acceptance guide 生成器
- [`export_localization_audit.py`](export_localization_audit.py): 書き出しパッケージ向け localization coverage / missing translation audit 生成器
- [`export_quality_reports.py`](export_quality_reports.py): 書き出し品質レポート bundle の共通オーケストレーション
- [`export_asset_rights.py`](export_asset_rights.py): 書き出しパッケージ向け asset rights / credits / AI provenance report 生成器
- [`export_audio_cue_sheet.py`](export_audio_cue_sheet.py): 書き出しパッケージ向け BGM / SFX / voice cue sheet と試聴確認レポート生成器
- [`export_stage_direction_sheet.py`](export_stage_direction_sheet.py): 書き出しパッケージ向け character stage direction / sprite presentation report 生成器
- [`export_presentation_timeline.py`](export_presentation_timeline.py): 書き出しパッケージ向け presentation timeline / pacing report 生成器
- [`export_choice_consequence_sheet.py`](export_choice_consequence_sheet.py): 書き出しパッケージ向け choice consequence / variable-effect audit report 生成器
- [`export_variable_influence_sheet.py`](export_variable_influence_sheet.py): 書き出しパッケージ向け variable definition / read-write influence audit report 生成器
- [`export_voice_production.py`](export_voice_production.py): 書き出しパッケージ向け voice recording sheet / delivery report 生成器
- [`export_release_readiness.py`](export_release_readiness.py): 書き出しパッケージ向け release-readiness summary / tester handoff gate 生成器
- [`export_story_route_map.py`](export_story_route_map.py): 書き出しパッケージ向け story route map / broken-link / unreachable-scene report 生成器
- [`export_route_playtest_workbook.py`](export_route_playtest_workbook.py): 書き出しパッケージ向け route playtest workbook / manual QA lane 生成器
- [`export_unlockable_manifest.py`](export_unlockable_manifest.py): 書き出し側の unlockable / gallery / replay カバレッジ manifest 生成器
- [`export_runtime_preload.py`](export_runtime_preload.py): 書き出し Runtime 向け preload manifest / performance report 生成器
- [`renpy_export.py`](renpy_export.py): Ren'Py Starter Bundle / `.rpy` migration export 生成器
- [`prototype_editor`](prototype_editor): エディタ frontend
- [`prototype_editor/modules`](prototype_editor/modules): ルート分析、ストーリーテンプレート、エディタ補助、Assistant、公開前チェックなどを扱う単体テスト可能な frontend 純ロジックモジュール
- [`export_player_template`](export_player_template): 書き出し後の Web Runtime テンプレート
- [`native_runtime`](native_runtime): ネイティブ Runtime player と desktop runtime 関連ロジック
- [`template_project`](template_project): 空白プロジェクトテンプレート
- [`tests`](tests): 自動 smoke / regression tests

## クイックスタート

ソースから起動する場合、基本的には Python 3 が必要です。

### 起動スクリプト

- macOS: [`start_editor.command`](start_editor.command) をダブルクリック
- Windows: [`start_editor.cmd`](start_editor.cmd) をダブルクリック
- Linux: [`start_editor.sh`](start_editor.sh) を実行

### コマンドライン

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

Windows の `py` launcher がない場合:

```bat
python run_editor.py
```

起動後、ブラウザでローカルの `127.0.0.1` アドレスが開きます。プロジェクトファイルは自分の PC 内に保存されます。

## 最初の Demo 作成

最初は小さく始めるのがおすすめです。

初めて触る場合は、Project Center でプレイ可能な Demo プロジェクトを作成し、最初のシーン、キャラクター、BGM、台詞が動くことを先に確認してください。その後、プレースホルダー素材と台詞を自分の内容に差し替えるのが最短です。

完全に空の状態から作りたい場合は、空白プロジェクトを作成してから starter kit を使うと、最初のキャラクター、背景、BGM を追加し、可能な範囲で最初のシーンにも接続できます。

すでにメモアプリや文書に台本を書いている場合は、ストーリーページの台本インポートパネルに短い範囲を貼り付けてください。`キャラクター: 台詞` は台詞、通常の行はナレーション、連続した `- 選択肢` は一つの選択肢カードとしてプレビュー後に挿入できます。

- 背景 1 枚
- キャラクター立ち絵 1 体
- BGM 1 曲
- 台詞 10 から 20 行
- 選択肢 1 つ
- 簡単なエンディング 1 つ

まず一本のルートを最後まで通し、その後で分岐、演出、UI、図鑑、ボイスなどを追加すると進めやすくなります。

## 多言語プロジェクト

Canvasia は初期 i18n フローに対応しています。

1. まずメイン言語でストーリーを完成させます。
2. プロジェクトの Runtime 設定でデフォルト言語を選びます。
3. `zh-CN`、`ja-JP`、`en-US` など、プレイヤーが切り替えられる言語を有効にします。
4. キャラクター名、シーン名、章名、台詞、ナレーション、選択肢の翻訳を追加します。
5. プロジェクト検査画面で多言語カバレッジレポートまたは CSV を書き出し、未翻訳や原文コピーの疑いがある項目を確認します。
6. CSV の翻訳列を入力し、対応しているキャラクター名、章名、シーン名、ストーリーカード翻訳をプロジェクトへインポートします。
7. Web Runtime またはネイティブ Runtime の設定メニューで言語切替を確認します。

翻訳が未入力の箇所はデフォルトテキストにフォールバックするため、一部の翻訳漏れでゲームが停止することはありません。

## 書き出し

プロジェクトを開き、プレビュー / 書き出し画面から次のパッケージを生成できます。

- Web 試遊パッケージ
- Ren'Py Starter Bundle パッケージ
- Windows desktop パッケージ
- macOS desktop パッケージ
- Linux desktop パッケージ
- standalone app ビルド用 scaffold を含むネイティブ Runtime preview パッケージ

気軽に共有するなら Web 試遊パッケージが最も簡単です。Web / desktop / native Runtime には `runtime_preload_manifest.json` と `RUNTIME_PRELOAD_REPORT.md` も含まれ、最初のシーンや序盤ルートの背景、立ち絵、音声を優先的に準備します。エディタの inspection page では、書き出し前に Runtime preload budget report を出力し、入口シーンの重い素材、欠落ファイル、シーン単位のロード hotspots を確認できます。ネイティブ Runtime は同じ manifest を読み込み、起動時は critical な画像と短い音声を優先キャッシュし、その後は小さな background queue で非 critical 素材を段階的に準備します。よりアプリに近いデスクトップ再生フローを検証する場合は、ネイティブ Runtime パッケージを使います。

Ren'Py Starter Bundle は `game/script.rpy`、`game/options.rpy`、`game/assets/` にコピーされた素材、migration manifest、カスタム Canvasia 演出の review notes、bundle quality report、label / jump / 参照ファイルを確認する local verifier script を含む zip を生成します。

すべての playable / runtime 書き出しには `README_试玩验收先看这里.md`、`story_route_map.json`、`story_route_map.md`、`route-playtest-workbook.json`、`route-playtest-workbook.md`、`route-playtest-workbook.csv`、`localization_audit.json`、`localization_audit.md`、`release_readiness_summary.json`、`release_readiness_summary.md`、`unlockable_content_manifest.json`、`unlockable_content_report.md`、`asset-rights-manifest.json`、`asset-rights-report.md`、`asset-rights-table.csv`、`audio-cue-sheet.json`、`audio-cue-report.md`、`audio-cue-table.csv`、`stage-direction-sheet.json`、`stage-direction-report.md`、`stage-direction-table.csv`、`presentation-timeline.json`、`presentation-timeline-report.md`、`presentation-timeline-table.csv`、`choice-consequence-sheet.json`、`choice-consequence-report.md`、`choice-consequence-table.csv`、`variable-influence-sheet.json`、`variable-influence-report.md`、`variable-influence-table.csv`、`voice-production-sheet.json`、`voice-production-report.md`、`voice-production-lines.csv` も同梱されます。README は起動手順と受け入れチェック、story route map は broken jumps / unreachable scenes / ending candidates の確認、route playtest workbook は分岐とエンディングを手動 QA lane、変数ヒント、修復優先タスク、CSV 行に整理します。localization audit は multilingual project の missing translations、release-readiness files はテスターへ渡せる状態かどうかの短い gate、unlockable JSON / Markdown は CG ギャラリー、音楽鑑賞、ボイス回想、キャラクター / 場所 / ナレーション / 関係アーカイブ、章回想、エンディング、実績の収録状況を確認するためのレポートです。asset-rights files は商用利用、出典、credit、placeholder、AI provenance の確認に使えます。audio-cue files は BGM の対象範囲、フェードイン / フェードアウト、停止位置、欠落した効果音、ボイス cue の準備状況を確認できます。stage-direction files は背景、立ち絵、表情、位置、スケール、透明度、レイヤー、入退場トランジションの準備状況を確認できます。presentation-timeline files は推定読了 / 演出時間、長い静的テキスト、視覚 / 音声アンカー不足、音楽の硬い切替、空選択肢、利用できないメディアを確認できます。choice-consequence files は選択肢テキスト、分岐先、変数効果、broken targets、重複選択肢、no-consequence buttons、release-blocking choice issues を確認できます。variable-influence files は変数定義、read/write locations、condition reads、unknown references、type mismatches、unused variables、written-but-never-read route flags を確認できます。voice-production files は録音用台詞表、推奨ファイル名、キャラクター別進捗、未バインド音声、長台詞レビューをまとめます。

補足: audio-cue report では、BGM がボイスやセリフを隠してしまう可能性がある mix risk も確認できます。

## Release パッケージ

Preview 版のエディタビルドは、利用可能な場合 GitHub Releases で配布されます。

- `macos.tar.gz`
- `windows.zip`
- `linux.tar.gz`

未署名の preview build は macOS Gatekeeper、Windows SmartScreen、ウイルス対策ソフトの警告を出す場合があります。必ず公式リポジトリの Release ページからダウンロードし、SHA-256 ファイルがある場合は検証してください。

## テスト

代表的なローカルチェック:

```bash
python3 -m unittest tests.test_run_editor_smoke -v
python3 -m unittest tests.test_frontend_particle_effects_module -v
node --check prototype_editor/app.js
node --check export_player_template/player.js
```

一部の browser / native rendering checks には追加のローカル依存関係が必要になる場合があります。

## ライセンス

このプロジェクトは [`LICENSE`](LICENSE) に含まれる Creator License 1.0 を使用します。このエンジンで制作したゲームの商用利用は可能ですが、改変したエンジン自体の再配布や商用化にはライセンス上の制限があります。

## Contributing

Issue や Pull Request を作成する前に、[`CONTRIBUTING.md`](CONTRIBUTING.md)、[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)、[`SECURITY.md`](SECURITY.md) を確認してください。
