# AI Interior Coordinator

間取り・予算・好みのテイストを入力するだけで、AIがインテリアコーディネートの提案と部屋の完成予想図を自動生成するWebアプリです。

## デモ

https://ai-interior-app-emuzu-trial.streamlit.app/

## 主な機能

- **インテリア提案**: 間取り・予算・テイストをもとに、AIが家具・小物を3〜5アイテム提案
- **予算管理**: 合計金額と予算の差をリアルタイム表示、予算超過時に警告
- **予算内訳チャート**: 各アイテムの金額をグラフで可視化
- **完成予想図生成**: 提案内容をもとにAIが部屋全体のレイアウト画像を生成（16:9）
- **楽天ショッピング連携**: 各提案アイテムに対し、楽天市場の類似商品を自動検索・表示

## 技術スタック

| 用途 | 技術 |
|---|---|
| フロントエンド | Streamlit |
| テキスト生成 | OpenAI GPT-4o mini（Structured Outputs） |
| 画像生成 | OpenAI DALL-E 3（1792×1024 / 16:9） |
| ショッピング検索 | 楽天商品検索API |
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
RAKUTEN_APP_ID=...
```

| キー | 取得先 |
|---|---|
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| `RAKUTEN_APP_ID` | https://webservice.rakuten.co.jp/ |

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
│   ├── openai_service.py         # テキスト生成（GPT-4o mini）
│   ├── dalle_service.py          # 画像生成（DALL-E 3）
│   └── shopping_api.py           # 楽天商品検索API
└── presentation.html             # プレゼン資料（GitHub Pages公開）
```

## 注意事項

- OpenAI APIは従量課金です。DALL-E 3の画像生成は1枚あたり約¥12かかります。
- 楽天商品検索APIは無料ですが、1秒1リクエストの制限があります。
- APIキーは `.env` または Streamlit Secrets で管理し、リポジトリにコミットしないでください。
