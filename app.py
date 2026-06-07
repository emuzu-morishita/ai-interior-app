import streamlit as st
import pandas as pd
import os
import html as html_lib
from datetime import datetime
from dotenv import load_dotenv

from services.openai_service import OpenAICoordinateGenerator
from services.openai_image_service import OpenAIImageGenerator
from services.shopping_api import search_all_items
from services.report import build_html_report, build_pdf_report, build_excel_report
from services import i18n
from services.i18n import t

load_dotenv()

st.set_page_config(page_title="AI Interior Coordinator", page_icon="🛋️", layout="wide")

# --- 全体スタイル（ヒーローバナー・商品カード） ---
st.markdown(
    """
<style>
.block-container { padding-top: 2.2rem; }

/* ヒーローバナー */
.hero { background: linear-gradient(120deg, #4d7c0f 0%, #84a98c 100%);
  border-radius: 22px; padding: 30px 40px; color: #ffffff; margin-bottom: 18px;
  box-shadow: 0 10px 28px rgba(77,124,15,0.20); }
.hero h1 { margin: 0; font-size: 36px; font-weight: 800; letter-spacing: .5px; color:#fff; }
.hero p { margin: 10px 0 0; font-size: 16px; opacity: .93; }

/* おすすめ商品カード（件数に関係なく固定サイズで表示） */
.sim-row { display: flex; flex-wrap: wrap; gap: 14px; margin: 8px 0 4px; }
.sim-card { width: 165px; background: #ffffff; border: 1px solid #e7e3d8;
  border-radius: 14px; padding: 10px; box-shadow: 0 2px 10px rgba(0,0,0,.05);
  transition: transform .15s ease, box-shadow .15s ease; }
.sim-card:hover { transform: translateY(-3px); box-shadow: 0 10px 22px rgba(0,0,0,.10); }
.sim-img { width: 100%; aspect-ratio: 1 / 1; border-radius: 10px;
  background-size: cover; background-position: center; background-color: #f1efe8; }
.sim-badge { display: inline-block; font-size: 10px; font-weight: 700; color: #4d7c0f;
  background: #eef3e3; border-radius: 6px; padding: 2px 7px; margin-top: 9px; }
.sim-name { font-size: 12px; line-height: 1.35; height: 34px; overflow: hidden;
  margin-top: 6px; color: #3a3a36; }
.sim-price { font-size: 17px; font-weight: 800; color: #2b2b28; margin-top: 6px; }
.sim-review { font-size: 11px; color: #9a8f7d; margin-top: 2px; }
.sim-btn { display: block; text-align: center; margin-top: 10px; padding: 7px 0;
  background: #4d7c0f; color: #fff !important; border-radius: 8px;
  text-decoration: none; font-size: 12px; font-weight: 700; }
.sim-btn:hover { background: #3f6a0c; }

/* サイドバー装飾 */
[data-testid="stSidebar"] { border-right: 1px solid #e7e3d8; }
.sb-brand { background: linear-gradient(135deg, #4d7c0f 0%, #84a98c 100%);
  border-radius: 16px; padding: 18px; color: #fff; margin: 0 0 16px; text-align: center;
  box-shadow: 0 6px 18px rgba(77,124,15,.18); }
.sb-brand .sb-ic { font-size: 30px; line-height: 1; }
.sb-brand .sb-tt { font-size: 17px; font-weight: 800; margin-top: 6px; }
.sb-brand .sb-sub { font-size: 10px; opacity: .9; margin-top: 3px; letter-spacing: 1.5px; }
.sb-h { font-size: 12px; font-weight: 800; color: #4d7c0f; letter-spacing: 1px;
  text-transform: uppercase; margin: 18px 0 9px; }
.sb-card { background: #ffffff; border: 1px solid #e7e3d8; border-left: 4px solid #4d7c0f;
  border-radius: 10px; padding: 12px 14px; font-size: 13px; color: #4a4a44; line-height: 1.65; }
.sb-step { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 11px; }
.sb-step .n { flex: none; width: 24px; height: 24px; border-radius: 50%; background: #4d7c0f;
  color: #fff; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.sb-step .tx { font-size: 13px; color: #3a3a36; line-height: 1.4; padding-top: 2px; }
.sb-link { display: block; text-align: center; margin-top: 8px; padding: 9px;
  background: #2b2b28; color: #fff !important; border-radius: 9px; text-decoration: none;
  font-size: 13px; font-weight: 700; }
.sb-link:hover { background: #4d7c0f; }

/* 保存（ダウンロード）ボタン：保存操作だと一目で分かるよう濃色で強調 */
[data-testid="stDownloadButton"] button { background: #2b2b28 !important;
  color: #fff !important; border: 0 !important; border-radius: 10px !important;
  font-weight: 700 !important; padding: 11px 0 !important;
  box-shadow: 0 4px 14px rgba(43,43,40,.18); transition: background .15s ease, transform .15s ease; }
[data-testid="stDownloadButton"] button:hover { background: #4d7c0f !important; transform: translateY(-1px); }
[data-testid="stDownloadButton"] button p { font-size: 15px !important; font-weight: 700 !important; }

/* 完成予想図の下に置く説明文ブロック */
.preview-desc { background: #f1efe8; border-left: 4px solid #4d7c0f;
  border-radius: 8px; padding: 12px 16px; margin: 12px 0 4px;
  font-size: 14px; color: #4a4a44; line-height: 1.65; }
</style>
""",
    unsafe_allow_html=True,
)


# --- APIキー: .env（ローカル開発）→ st.secrets（本番）の順で取得 ---
def _get_secret(key: str) -> str:
    val = os.getenv(key, "")
    if not val:
        try:
            val = st.secrets[key]
        except Exception:
            val = ""
    return val


def _render_products(products, lang: str) -> str:
    """おすすめ商品を固定サイズのHTMLカード列としてレンダリングする。"""
    cards = []
    for p in products:
        name = html_lib.escape(p.name[:40] + ("…" if len(p.name) > 40 else ""))
        badge = html_lib.escape(p.source)
        img = html_lib.escape(p.image_url or "", quote=True)
        url = html_lib.escape(p.url or "", quote=True)
        review = ""
        if p.review_average > 0:
            review = f'<div class="sim-review">{t(lang, "review_fmt", avg=p.review_average, count=p.review_count)}</div>'
        cards.append(
            f'<div class="sim-card">'
            f'<div class="sim-img" style="background-image:url(\'{img}\')"></div>'
            f'<span class="sim-badge">🏷️ {badge}</span>'
            f'<div class="sim-name">{name}</div>'
            f'<div class="sim-price">¥{p.price:,}</div>'
            f'{review}'
            f'<a class="sim-btn" href="{url}" target="_blank" rel="noopener">{t(lang, "product_button")}</a>'
            f'</div>'
        )
    return f'<div class="sim-row">{"".join(cards)}</div>'


OPENAI_KEY = _get_secret("OPENAI_API_KEY")
RAKUTEN_APP_ID = _get_secret("RAKUTEN_APP_ID")
RAKUTEN_ACCESS_KEY = _get_secret("RAKUTEN_ACCESS_KEY")
RAKUTEN_ORIGIN = _get_secret("RAKUTEN_ORIGIN")
YAHOO_APP_ID = _get_secret("YAHOO_APP_ID")

# --- サイドバー：ブランドカード + 言語選択（最初に決定） ---
PRESENTATION_URL = "https://emuzu-morishita.github.io/ai-interior-app/presentation.html"

st.sidebar.markdown(
    '<div class="sb-brand"><div class="sb-ic">🛋️</div>'
    '<div class="sb-tt">AI Interior Coordinator</div>'
    '<div class="sb-sub">AI INTERIOR STUDIO</div></div>',
    unsafe_allow_html=True,
)

lang = st.sidebar.selectbox(
    "🌐 Language / 言語",
    list(i18n.LANGUAGES.keys()),
    format_func=lambda c: i18n.LANGUAGES[c],
)

st.markdown(
    f'<div class="hero"><h1>🛋️ AI Interior Coordinator</h1>'
    f'<p>{html_lib.escape(t(lang, "caption"))}</p></div>',
    unsafe_allow_html=True,
)

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

# --- サイドバー本体 ---
with st.sidebar:
    st.markdown(f'<div class="sb-h">ℹ️ {html_lib.escape(t(lang, "about_header"))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sb-card">{html_lib.escape(t(lang, "about_body"))}</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="sb-h">✨ {html_lib.escape(t(lang, "how_header"))}</div>', unsafe_allow_html=True)
    steps_html = "".join(
        f'<div class="sb-step"><div class="n">{i}</div>'
        f'<div class="tx">{html_lib.escape(t(lang, f"step{i}"))}</div></div>'
        for i in (1, 2, 3)
    )
    st.markdown(steps_html, unsafe_allow_html=True)

    st.markdown(
        f'<a class="sb-link" href="{PRESENTATION_URL}" target="_blank" rel="noopener">'
        f'📊 {html_lib.escape(t(lang, "presentation_link"))}</a>',
        unsafe_allow_html=True,
    )

# --- ユーザー入力 ---
col_l, col_r = st.columns([1, 1])
with col_l:
    room_idx = st.selectbox(
        t(lang, "room_size_label"),
        range(len(i18n.ROOM_SIZE_PROMPT)),
        format_func=lambda i: i18n.ROOM_SIZE_LABELS[lang][i],
    )
    taste_other = t(lang, "taste_other")
    taste_choice = st.selectbox(t(lang, "taste_label"), i18n.TASTE_OPTIONS[lang] + [taste_other])
    if taste_choice == taste_other:
        taste = st.text_input(
            t(lang, "taste_other_label"), "", placeholder=i18n.TASTE_DEFAULT[lang]
        ).strip() or i18n.TASTE_DEFAULT[lang]
    else:
        taste = taste_choice
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
    shopping_enabled = (RAKUTEN_APP_ID and RAKUTEN_ACCESS_KEY) or YAHOO_APP_ID
    if st.session_state.coord_items and shopping_enabled:
        with st.spinner(t(lang, "spinner_shopping")):
            try:
                st.session_state.shopping_results = search_all_items(
                    st.session_state.coord_items,
                    rakuten_id=RAKUTEN_APP_ID,
                    rakuten_access_key=RAKUTEN_ACCESS_KEY,
                    rakuten_origin=RAKUTEN_ORIGIN,
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

    # 1. 完成予想図（一番上） ※画像が無い場合は見出しごとスキップ
    if st.session_state.room_image:
        st.subheader("🖼️ " + t(lang, "preview_header"))
        st.image(st.session_state.room_image, use_container_width=True)
        st.markdown(
            f'<div class="preview-desc">💡 {html_lib.escape(t(lang, "preview_caption"))}</div>',
            unsafe_allow_html=True,
        )

    # 2. 提案アイテム一覧
    st.subheader("🛋️ " + t(lang, "items_header"))
    for i, item in enumerate(items, 1):
        with st.expander(f"{i}. {item['item_name']} — ¥{item['price']:,}", expanded=True):
            st.write(item["reason"])
            products = shopping_results.get(item["item_name"], [])
            if products:
                st.markdown(f"**{t(lang, 'recommend_header')}**")
                st.markdown(_render_products(products, lang), unsafe_allow_html=True)
            elif (RAKUTEN_APP_ID and RAKUTEN_ACCESS_KEY) or YAHOO_APP_ID:
                st.caption(t(lang, "no_products"))

    # 3. 値段等の概要（メトリクス + 予算内訳）
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

    st.subheader("📊 " + t(lang, "budget_breakdown"))
    chart_data = pd.DataFrame({
        t(lang, "chart_item"): [item["item_name"] for item in items],
        t(lang, "chart_price"): [item["price"] for item in items],
    })
    st.bar_chart(chart_data.set_index(t(lang, "chart_item")))

    # 4. 保存ボタン（最後）：リロードで消える前に好きな形式で手元に残す
    st.markdown("---")
    fmt = st.radio(t(lang, "save_format_label"), ["HTML", "PDF", "Excel"], horizontal=True)
    report_args = (items, shopping_results, st.session_state.room_image)
    report_kwargs = dict(
        lang=lang,
        room_label=i18n.ROOM_SIZE_LABELS[lang][room_idx],
        taste=taste,
        budget=budget,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    _XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    builders = {
        "HTML": (build_html_report, "html", "text/html"),
        "PDF": (build_pdf_report, "pdf", "application/pdf"),
        "Excel": (build_excel_report, "xlsx", _XLSX_MIME),
    }
    builder, ext, mime = builders[fmt]
    try:
        data = builder(*report_args, **report_kwargs)
        st.download_button(
            t(lang, "download_btn"),
            data=data,
            file_name=f"ai-interior-proposal_{stamp}.{ext}",
            mime=mime,
            use_container_width=True,
        )
    except Exception as e:
        st.warning(t(lang, "warn_save", e=e))
    st.caption(t(lang, "download_caption"))
