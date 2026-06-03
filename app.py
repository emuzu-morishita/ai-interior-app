import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

from services.openai_service import OpenAICoordinateGenerator
from services.openai_image_service import OpenAIImageGenerator
from services.shopping_api import search_all_items
from services import i18n
from services.i18n import t

load_dotenv()

st.set_page_config(page_title="AI Interior Coordinator", layout="wide")


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

# --- 言語選択（最初に決定し、以降の全文言・AI呼び出しに反映） ---
lang = st.sidebar.selectbox(
    "🌐 Language / 言語",
    list(i18n.LANGUAGES.keys()),
    format_func=lambda c: i18n.LANGUAGES[c],
)

st.title("AI Interior Coordinator")
st.caption(t(lang, "caption"))

if not OPENAI_KEY:
    st.error(t(lang, "err_no_openai"))
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
    st.markdown("---")
    st.header(t(lang, "about_header"))
    st.write(t(lang, "about_body"))
    st.markdown("---")
    st.page_link(
        "https://emuzu-morishita.github.io/ai-interior-app/presentation.html",
        label=t(lang, "presentation_link"),
    )

# --- ユーザー入力 ---
col_l, col_r = st.columns([1, 1])
with col_l:
    room_idx = st.selectbox(
        t(lang, "room_size_label"),
        range(len(i18n.ROOM_SIZE_PROMPT)),
        format_func=lambda i: i18n.ROOM_SIZE_LABELS[lang][i],
    )
    taste = st.text_input(t(lang, "taste_label"), i18n.TASTE_DEFAULT[lang])
with col_r:
    budget = st.number_input(t(lang, "budget_label"), min_value=5000, max_value=1000000, value=50000, step=5000)
    st.metric(t(lang, "budget_metric"), f"¥{budget:,}")

room_prompt = i18n.ROOM_SIZE_PROMPT[room_idx]
language_name = i18n.LANGUAGE_NAMES[lang]

if st.button(t(lang, "generate_btn"), type="primary", use_container_width=True):
    # ボタンを押した瞬間に前回の結果・エラーをクリア
    st.session_state.coord_items = None
    st.session_state.shopping_results = {}
    st.session_state.room_image = None
    st.session_state.error = None

    # --- 1. コーディネート生成 ---
    with st.spinner(t(lang, "spinner_coordinate")):
        try:
            st.session_state.coord_items = OpenAICoordinateGenerator(OPENAI_KEY).generate(
                room_prompt, budget, taste, language_name
            )
        except Exception as e:
            st.session_state.error = t(lang, "err_coordinate", e=e)

    # --- 2. 商品検索（楽天・Yahoo!を並列） ---
    if st.session_state.coord_items and (RAKUTEN_APP_ID or YAHOO_APP_ID):
        with st.spinner(t(lang, "spinner_shopping")):
            try:
                st.session_state.shopping_results = search_all_items(
                    st.session_state.coord_items,
                    rakuten_id=RAKUTEN_APP_ID,
                    yahoo_id=YAHOO_APP_ID,
                )
            except Exception as e:
                st.warning(t(lang, "warn_shopping", e=e))

    # --- 3. 画像生成 ---
    if st.session_state.coord_items:
        with st.spinner(t(lang, "spinner_image")):
            try:
                st.session_state.room_image = OpenAIImageGenerator(OPENAI_KEY).generate(
                    st.session_state.coord_items[0]["image_prompt"]
                )
            except Exception as e:
                st.warning(t(lang, "warn_image", e=e))

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
    m1.metric(t(lang, "m_count"), t(lang, "count_unit", n=len(items)))
    m2.metric(t(lang, "m_total"), f"¥{total_price:,}")
    diff_label = t(lang, "diff_over") if over_budget else t(lang, "diff_under")
    m3.metric(
        t(lang, "m_diff"),
        f"{diff_label} ¥{abs(remaining):,}",
        delta=remaining,
        delta_color="inverse",
    )
    if over_budget:
        st.warning(t(lang, "warn_over", amount=abs(remaining)))

    st.subheader(t(lang, "budget_breakdown"))
    chart_data = pd.DataFrame({
        t(lang, "chart_item"): [item["item_name"] for item in items],
        t(lang, "chart_price"): [item["price"] for item in items],
    })
    st.bar_chart(chart_data.set_index(t(lang, "chart_item")))

    st.subheader(t(lang, "items_header"))
    for i, item in enumerate(items, 1):
        with st.expander(f"{i}. {item['item_name']} — ¥{item['price']:,}", expanded=True):
            st.write(item["reason"])
            products = shopping_results.get(item["item_name"], [])
            if products:
                st.markdown(f"**{t(lang, 'similar_header')}**")
                cols = st.columns(len(products))
                for col, product in zip(cols, products):
                    with col:
                        if product.image_url:
                            st.image(product.image_url, use_container_width=True)
                        st.caption(f"🏷️ {product.source}")
                        st.markdown(f"**{product.name[:40]}{'…' if len(product.name) > 40 else ''}**")
                        st.markdown(f"¥{product.price:,}")
                        if product.review_average > 0:
                            st.caption(t(lang, "review_fmt", avg=product.review_average, count=product.review_count))
                        st.link_button(t(lang, "product_button"), product.url, use_container_width=True)
            elif RAKUTEN_APP_ID or YAHOO_APP_ID:
                st.caption(t(lang, "no_products"))

    st.markdown("---")
    st.subheader(t(lang, "preview_header"))
    if st.session_state.room_image:
        st.image(st.session_state.room_image, caption=t(lang, "preview_caption"), use_container_width=True)
