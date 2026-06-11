# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 初回投稿プロンプト
はじめまして。
私はシステムエンジニアです。入社7年目の中堅です。
今回、社内イベントにて一人でAI駆動開発を行うため、それに向けて一から設計をしていきたいと考えています。
期限は6月30日までですが、デプロイまで行い、社長 及び 社員がサイト上、又はアプリをインストールして確認できる状態にしなければなりません。
あと、プレゼン資料も用意する必要があります。
これまでお話した内容は前提となります。

ここから本題の"私の作りたいもの"についてです。
私が作りたいものは、部屋の間取りに対して、自分がどんな雰囲気の部屋にしたいかを入力すると、どんな家具でどんな配置にすれば、思い通りの部屋のレイアウトになるのかを提案してくれるものです。

部屋の模様替えが得意な方は問題ないかと思いますが、苦手な方向けに、参考程度にどんな家具を使って、どんな配置にすれば理想の部屋になっていくのかを一緒に探れるようなもの考えています。
実際自分も部屋のレイアウト決めには悩まされたりしているので、それがあると大分変わるのでは？と思いました。
家具についても、どんな感じの家具を使用するかの提案をするだけでなく、それに類似する商品をAmazonやYahoo!ショッピング等で提示してくれるような機能も付けたいと考えています。
ただ、これには使用者の予算等もあると思うので、その予算に合った商品を提案するようにしたいです。
その予算もできればユーザーに指定してもらうように入力フォームがあるといいです。

以上をまず読んでいただいて、実現可能であるかどうかや、実現可能である場合はどのようなものを準備する必要があるのかなどをお聞きしたいです。
あとは、既存で同様なアプリやサイトがないかを予め確認しておきたいです。
著作権侵害とならないよう注意が必要なためです。

以上、よろしくお願い致します。


## 概要

間取り・予算・テイストを入力すると、AI がインテリア提案・完成予想図・類似商品（楽天/Yahoo!）をまとめて返す Streamlit 製 Web アプリ。Streamlit Cloud にデプロイされている（https://ai-interior-app-emuzu-trial.streamlit.app/）。

## 開発コマンド

```bash
# 仮想環境（リポジトリ直下に venv/ がコミット対象外で存在）
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# ローカル起動 → http://localhost:8501
streamlit run app.py
```

- lint・型チェックのツールは未導入。変更後の確認は次の2段階:
  1. `venv\Scripts\python.exe -m py_compile app.py services\*.py` で構文チェック
  2. `venv\Scripts\python.exe tests\smoke_test.py` — OpenAI・楽天・Yahoo! をフェイクに差し替えて全フロー（生成→結果表示→レポート3形式→個別再生成→プレビュー更新）を AppTest で検証する。**API課金なしで実行できる**ので変更後は必ず流すこと。i18n の4言語キーパリティもここで検証される。
  最終確認は `streamlit run app.py` での実機確認。
- このマシンの `python` コマンドは Microsoft Store のスタブのため使わない。常に `venv\Scripts\python.exe` を明示すること。
- APIキーは `.env`（ローカル）に置く。`.env.example` をコピーして使う。本番は Streamlit Cloud の Secrets。

## アーキテクチャ

**`app.py` が UI とオーケストレーション両方を担う単一ファイル。** `services/` は機能ごとのモジュール。新機能は基本ここに足す。

### 生成パイプライン（「生成する」ボタン押下時、`app.py` 内で実行）

1. **コーディネート生成** — `OpenAICoordinateGenerator.generate()` が GPT-4o mini の Structured Outputs で `{"items": [{item_name, price, reason, placement, search_keyword}], "room_image_prompt": "..."}` を返す
2. **商品検索** — `search_all_items()` が各アイテムの `search_keyword`（常に日本語）で楽天・Yahoo! を **ThreadPoolExecutor で並列検索**し `{item_name: [ShoppingItem]}` を返す
3. **画像生成** — `OpenAIImageGenerator.generate()` が `room_image_prompt`（全アイテムを配置した部屋全体の英語プロンプト）を gpt-image-1 に渡し横長（1536×1024）の完成予想図を生成

**ステップ 2 と 3 は互いに独立なため `ThreadPoolExecutor` で並列実行**して待ち時間を短縮している。結果はすべて `st.session_state`（`coord_items` / `shopping_results` / `room_image` / `error`）に保持。ブラウザのリロードで消えるため、最後に HTML/PDF/Excel での保存（ダウンロード）機能を置いている。**ステップ 2・3 は失敗しても警告のみ（graceful degradation）で、コーディネート提案自体は表示される。**

### 重要な設計上の約束

- **`room_image_prompt` は UI 言語にかかわらず常に英語**（画像生成精度のため）、**`search_keyword` は常に日本語**（楽天・Yahoo! は日本のモールのため。英/韓/中 UI でも商品がヒットする）。いずれも `services/prompt.py` のプロンプトで明示。`item_name`・`reason`・`placement` のみ選択言語。
- **結果表示とレポートの金額・条件は `st.session_state.gen_ctx`（生成時の条件）基準**。生成後にユーザーが予算等のウィジェットを動かしても表示が狂わないようにするため。現在の入力値を直接使わない。
- **プロバイダー抽象** — `services/base.py` に `CoordinateGeneratorBase` / `ImageGeneratorBase` の ABC があるが、実装は OpenAI のみ。別プロバイダーを足すならこのインターフェースに従う。
- **シークレット取得は `_get_secret()` 経由**（`app.py`）。`os.getenv`（.env）→ `st.secrets`（本番）の順でフォールバック。直接 `os.getenv` / `st.secrets` を呼ばない。
- **楽天 API は 2026年2月刷新後の新エンドポイント**（`openapi.rakuten.co.jp/...`）。`applicationId`(UUID) + `accessKey`(pk_...) の両方と、登録ドメインに一致する `Origin`/`Referer` ヘッダーが必須。両キーが揃った時のみ実行。Yahoo! は `YAHOO_APP_ID` のみで動く。
- `ShoppingItem`（dataclass）は `services/shopping_api.py` で定義。Yahoo 側は循環参照回避のため遅延 import している。

### 多言語対応（`services/i18n.py`）

- 全 UI 文言は `TRANSLATIONS[lang][key]` の辞書。`t(lang, key, **kwargs)` でアクセス（`str.format` でプレースホルダ展開、未定義キーは日本語フォールバック）。
- **UI 文言を追加・変更するときは ja / en / ko / zh / pt の 5 言語すべてにキーを追加すること。** 1 言語でも欠けると、その言語でキー文字列がそのまま表示される（キーパリティは `tests/smoke_test.py` が検証する）。
- `LANGUAGE_NAMES`（AIプロンプト用の英語言語名）、`ROOM_SIZE_PROMPT`（AI用の英語寸法。表示ラベル `ROOM_SIZE_LABELS` とは別物）、`TASTE_OPTIONS`/`TASTE_DEFAULT` も言語別に定義。

### レポート出力（`services/report.py`）

- `build_html_report` / `build_pdf_report` / `build_excel_report` の 3 ビルダー。**いずれも同じ引数シグネチャ**（`items, shopping_results, room_image, *, lang, room_label, taste, budget, generated_at, owned_items=""`）。`app.py` の `builders` dict で形式を切り替える。
- 提案条件の (ラベル, 値) は `_conditions()` で共通化。
- HTML は画像を base64 data URI で埋め込み外部依存ゼロ。PDF は reportlab + **言語別 CID フォント**（`_PDF_CID_FONTS`、ja/ko/zh のみ。追加フォントファイル不要、失敗時 Helvetica）。en/pt などラテン文字言語は Helvetica（cp1252 でアクセント文字も表示可）で出力される。

## 既知の注意点

- 初回投稿プロンプトに沿った開発ができているかどうか。
- Streamlit Cloud はモジュールキャッシュにより i18n の新キーが即時反映されないことがある（過去に発生）。デプロイ後に文言が反映されない場合はアプリの再起動（reboot）を試す。
- gpt-image-1 の画像生成は 1 枚あたり数円〜十数円の従量課金。Gemini 無料枠のような制限とは別に、コスト意識が必要。
