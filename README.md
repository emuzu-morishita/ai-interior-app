# AI Interior Coordinator

間取り・予算・好みのテイストを入力するだけで、AIがインテリアコーディネートの提案と部屋の完成予想図を自動生成するWebアプリです。

## デモ

https://ai-interior-app-emuzu-trial.streamlit.app/

## 主な機能

- **インテリア提案**: 間取り・予算・テイストをもとに、AIが家具・小物を3〜5アイテム提案
- **予算管理**: 合計金額と予算の差をリアルタイム表示、予算超過時に警告
- **予算内訳チャート**: 各アイテムの金額をグラフで可視化
- **完成予想図生成**: 提案内容をもとにAIが部屋全体のレイアウト画像を生成（横長）
- **ショッピング連携**: 各提案アイテムに対し、楽天市場・Yahoo!ショッピングの類似商品を自動検索・表示
- **多言語対応**: 日本語 / English / 한국어 / 中文 / Português (Brasil) を切替可能。AIの提案文も選択言語で生成

## 技術スタック

| 用途 | 技術 |
|---|---|
| フロントエンド | Streamlit |
| テキスト生成 | OpenAI GPT-4o mini（Structured Outputs） |
| 画像生成 | OpenAI gpt-image-1（1536×1024 / 横長） |
| ショッピング検索 | 楽天商品検索API / Yahoo!ショッピングAPI |
| 多言語 | 日本語・英語・韓国語・中国語・ポルトガル語(ブラジル)（services/i18n.py） |
| デプロイ | Streamlit Cloud |

## セットアップ（ローカル開発）

### 1. リポジトリをクローン

```bash
git clone https://github.com/emuzu-morishita/ai-interior-app.git
cd ai-interior-app
```

### 2. 仮想環境を作成・有効化

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. 依存パッケージをインストール

```bash
pip install -r requirements.txt
```

### 4. APIキーを設定

`.env.example` をコピーして `.env` を作成し、各APIキーを設定します。

```bash
cp .env.example .env
```

```env
OPENAI_API_KEY=sk-...
RAKUTEN_APP_ID=...            # UUID形式のapplicationId
RAKUTEN_ACCESS_KEY=pk_...     # pk_で始まるアクセスキー
RAKUTEN_ORIGIN=https://...    # 登録した「許可されたWebサイト」
YAHOO_APP_ID=...              # Yahoo!ショッピングのClient ID
```

| キー | 取得先 |
|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `RAKUTEN_APP_ID` / `RAKUTEN_ACCESS_KEY` | https://webservice.rakuten.co.jp/ （2026年新仕様：ID+キー必須） |
| `YAHOO_APP_ID` | https://e.developer.yahoo.co.jp/register |

### 5. アプリを起動

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 にアクセスしてください。

## デプロイ（Streamlit Cloud）

1. [Streamlit Cloud](https://streamlit.io/cloud) でリポジトリを連携
2. **App settings → Secrets** に以下を設定（`.streamlit/secrets.toml.example` 参照）

```toml
OPENAI_API_KEY = "sk-..."
RAKUTEN_APP_ID = "..."
RAKUTEN_ACCESS_KEY = "pk_..."
RAKUTEN_ORIGIN = "https://..."
YAHOO_APP_ID = "..."
```

## プロジェクト構成

```
ai-interior-app/
├── app.py                        # メインアプリ（Streamlit UI）
├── requirements.txt
├── .env.example                  # 環境変数のサンプル
├── .streamlit/
│   └── secrets.toml.example      # Streamlit Cloud用Secretsサンプル
├── services/
│   ├── base.py                   # プロバイダー抽象インターフェース
│   ├── prompt.py                 # 共通プロンプト・JSONスキーマ定義
│   ├── i18n.py                   # 多言語対応（日/英/韓/中）
│   ├── openai_service.py         # テキスト生成（GPT-4o mini）
│   ├── openai_image_service.py   # 画像生成（gpt-image-1）
│   ├── shopping_api.py           # 楽天商品検索API
│   └── yahoo_shopping_api.py     # Yahoo!ショッピング検索API
└── presentation.html             # プレゼン資料（GitHub Pages公開）
```

## 注意事項

- OpenAI APIは従量課金です。gpt-image-1 の画像生成は1枚あたり数円〜十数円程度かかります。
- 楽天・Yahoo!ショッピングの商品検索APIは無料ですが、リクエスト数の制限があります。
- APIキーは `.env` または Streamlit Secrets で管理し、リポジトリにコミットしないでください。
