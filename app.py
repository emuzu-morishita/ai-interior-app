import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

from services.openai_service import OpenAICoordinateGenerator
from services.dalle_service import DallEImageGenerator
from services.shopping_api import search_all_items

load_dotenv()

st.set_page_config(page_title="AI Interior Coordinator", layout="wide")
st.title("AI Interior Coordinator")
st.caption("間取り・予算・テイストを入力するだけで、AIがインテリアコーディネートと完成予想図を提案します。")

# --- APIキー: .env（ローカル開発）→ st.secrets（本番）の順で取得 ---
def _get_secret(key: str) -> str:
    val = os.getenv(key, "")
    if not val:
        try:
            val = st.secrets[key]
        except Exception:
            val = ""
    return val

OPENAI_KEY = _get_secret("OPENAI_API_KEY")
RAKUTEN_APP_ID = _get_secret("RAKUTEN_APP_ID")
YAHOO_APP_ID = _get_secret("YAHOO_APP_ID")

if not OPENAI_KEY:
    st.error("OPENAI_API_KEY が設定されていません。Streamlit Secrets または .env を確認してください。")
    st.stop()

# --- セッション状態の初期化 ---
if "coord_items" not in st.session_state:
    st.session_state.coord_items = None
if "shopping_results" not in st.session_state:
    st.session_state.shopping_results = {}
if "room_image" not in st.session_state:
    st.session_state.room_image = None
if "error" not in st.session_state:
    st.session_state.error = None

# --- サイドバー ---
with st.sidebar:
    st.header("このアプリについて")
    st.write(
        "OpenAI GPT-4o mini が家具・インテリアを提案し、"
        "DALL-E 3 が部屋の完成予想図を生成します。"
        "楽天市場・Yahoo!ショッピングで類似商品も検索できます。"
    )
    st.markdown("---")
    st.page_link(
        "https://emuzu-morishita.github.io/ai-interior-app/presentation.html",
        label="プレゼン資料を見る",
    )

# --- ユーザー入力 ---
col_l, col_r = st.columns([1, 1])
with col_l:
    room_size = st.selectbox("間取り（広さ）", ["6畳", "8畳", "10畳", "12畳以上"])
    taste = st.text_input("好みのテイスト（例：北欧モダン、インダストリアル）", "北欧モダン")
with col_r:
    budget = st.number_input("予算 (円)", min_value=5000, max_value=1000000, value=50000, step=5000)
    st.metric("設定予算", f"¥{budget:,}")

if st.button("コーディネートを生成する", type="primary", use_container_width=True):
    # ボタンを押した瞬間に前回の結果・エラーをクリア
    st.session_state.coord_items = None
    st.session_state.shopping_results = {}
    st.session_state.room_image = None
    st.session_state.error = None

    # --- 1. コーディネート生成 ---
    with st.spinner("AIがコーディネートを考えています..."):
        try:
            st.session_state.coord_items = OpenAICoordinateGenerator(OPENAI_KEY).generate(room_size, budget, taste)
        except Exception as e:
            st.session_state.error = f"コーディネート生成に失敗しました: {e}"

    # --- 2. 商品検索（楽天・Yahoo!を並列） ---
    if st.session_state.coord_items and (RAKUTEN_APP_ID or YAHOO_APP_ID):
        with st.spinner("楽天・Yahoo!ショッピングで類似商品を検索しています..."):
            try:
                st.session_state.shopping_results = search_all_items(
                    st.session_state.coord_items,
                    rakuten_id=RAKUTEN_APP_ID,
                    yahoo_id=YAHOO_APP_ID,
                )
            except Exception as e:
                st.warning(f"ショッピング検索に失敗しました（コーディネート提案は表示されます）: {e}")

    # --- 3. 画像生成 ---
    if st.session_state.coord_items:
        with st.spinner("完成予想図を生成中...（約10〜20秒）"):
            try:
                st.session_state.room_image = DallEImageGenerator(OPENAI_KEY).generate(
                    st.session_state.coord_items[0]["image_prompt"]
                )
            except Exception as e:
                st.warning(f"画像生成に失敗しました: {e}")

# --- エラー表示 ---
if st.session_state.error:
    st.error(st.session_state.error)

# --- 結果表示 ---
if st.session_state.coord_items:
    items = st.session_state.coord_items
    shopping_results = st.session_state.shopping_results

    total_price = sum(item["price"] for item in items)
    remaining = budget - total_price
    over_budget = remaining < 0

    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric("提案アイテム数", f"{len(items)} 点")
    m2.metric("合計金額（目安）", f"¥{total_price:,}")
    m3.metric(
        "予算との差",
        f"{'超過' if over_budget else '余り'} ¥{abs(remaining):,}",
        delta=remaining,
        delta_color="inverse",
    )
    if over_budget:
        st.warning(f"合計金額が予算を ¥{abs(remaining):,} 超過しています。")

    st.subheader("予算内訳")
    chart_data = pd.DataFrame({
        "アイテム": [item["item_name"] for item in items],
        "金額": [item["price"] for item in items],
    })
    st.bar_chart(chart_data.set_index("アイテム"))

    st.subheader("提案アイテム一覧")
    for i, item in enumerate(items, 1):
        with st.expander(f"{i}. {item['item_name']} — ¥{item['price']:,}", expanded=True):
            st.write(item["reason"])
            products = shopping_results.get(item["item_name"], [])
            if products:
                st.markdown("**見つかった類似商品（楽天・Yahoo!）**")
                cols = st.columns(len(products))
                for col, product in zip(cols, products):
                    with col:
                        if product.image_url:
                            st.image(product.image_url, use_container_width=True)
                        st.caption(f"🏷️ {product.source}")
                        st.markdown(f"**{product.name[:40]}{'…' if len(product.name) > 40 else ''}**")
                        st.markdown(f"¥{product.price:,}")
                        if product.review_average > 0:
                            st.caption(f"★ {product.review_average:.1f}（{product.review_count:,}件）")
                        st.link_button("商品ページへ →", product.url, use_container_width=True)
            elif RAKUTEN_APP_ID or YAHOO_APP_ID:
                st.caption("該当する商品が見つかりませんでした。")

    st.markdown("---")
    st.subheader("完成予想図（AI生成）")
    if st.session_state.room_image:
        st.image(st.session_state.room_image, caption="AIが提案する理想のレイアウト", use_container_width=True)
