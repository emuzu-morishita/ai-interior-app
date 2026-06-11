import streamlit as st
import pandas as pd
import base64
import os
import html as html_lib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image

from services.openai_service import OpenAICoordinateGenerator
from services.openai_image_service import OpenAIImageGenerator
from services.shopping_api import search_all_items
from services.report import build_html_report, build_pdf_report, build_excel_report
from services import i18n
from services.i18n import t

load_dotenv()

st.set_page_config(page_title="AI Interior Coordinator", page_icon="🛋️", layout="wide")

# --- 全体スタイル ---
st.markdown(
    """
<style>
/* ── CSS 変数 ─────────────────────────────────── */
:root {
  --brand:    #4d7c0f;
  --brand-dk: #3a5f0b;
  --brand-lt: #84a98c;
  --card:     #ffffff;
  --border:   #e7e3d8;
  --text:     #2b2b28;
  --text-md:  #4a4a44;
  --text-sm:  #6b6b5f;
  --r-sm:  10px;
  --r-md:  14px;
  --r-lg:  22px;
  --sh-sm: 0 2px 8px rgba(0,0,0,.06);
  --sh-md: 0 6px 22px rgba(0,0,0,.10);
  --ease:  0.18s cubic-bezier(0.4,0,0.2,1);
}

/* ── モーション抑制（アクセシビリティ） ──────── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* ── Streamlit 既定UIを隠す（商用アプリらしくヘッダーをすっきり） ── */
[data-testid="stToolbar"]      { display: none !important; }  /* 右上 Deploy/⋮ メニュー */
[data-testid="stDeployButton"] { display: none !important; }  /* Deploy ボタン */
[data-testid="stDecoration"]   { display: none !important; }  /* 上部の虹色ライン */
#MainMenu                      { visibility: hidden; }
footer                         { visibility: hidden; }
[data-testid="stHeader"]       { background: transparent; }   /* ヘッダー帯を透明化（サイドバー開閉ボタンは残す） */

/* ── レイアウト ─────────────────────────────── */
.block-container { padding-top: 2.2rem; }

/* ── ヒーローバナー ─────────────────────────── */
.hero {
  background: linear-gradient(135deg, #2e4d08 0%, #4d7c0f 50%, #7aab55 100%);
  border-radius: var(--r-lg); padding: 34px 44px; color: #fff; margin-bottom: 22px;
  box-shadow: 0 12px 40px rgba(77,124,15,.25), inset 0 1px 0 rgba(255,255,255,.12);
  position: relative; overflow: hidden;
}
.hero::after {
  content: ''; position: absolute; top: -80px; right: -80px;
  width: 380px; height: 380px;
  background: radial-gradient(circle, rgba(255,255,255,.07) 0%, transparent 65%);
  border-radius: 50%; pointer-events: none;
}
.hero h1 {
  margin: 0; font-size: 36px; font-weight: 800; letter-spacing: -0.3px; color: #fff;
  text-wrap: balance; position: relative;
}
.hero p { margin: 10px 0 0; font-size: 16px; opacity: .92; text-wrap: pretty; position: relative; }

/* ── おすすめ商品カード ─────────────────────── */
.sim-row { display: flex; flex-wrap: wrap; gap: 14px; margin: 8px 0 4px; }
.sim-card {
  width: 165px; background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 12px; box-shadow: var(--sh-sm);
  transition: transform var(--ease), box-shadow var(--ease), border-color var(--ease);
}
.sim-card:hover { transform: translateY(-4px); box-shadow: var(--sh-md); border-color: #c5d9a8; }
.sim-img {
  width: 100%; aspect-ratio: 1 / 1; border-radius: var(--r-sm);
  background-size: cover; background-position: center; background-color: #f1efe8;
}
.sim-badge {
  display: inline-block; font-size: 10px; font-weight: 700; color: var(--brand);
  background: #eef3e3; border-radius: 6px; padding: 2px 7px; margin-top: 9px;
}
.sim-name { font-size: 12px; line-height: 1.4; height: 34px; overflow: hidden; margin-top: 6px; color: var(--text-md); }
.sim-price { font-size: 17px; font-weight: 800; color: var(--text); margin-top: 6px; font-variant-numeric: tabular-nums; }
.sim-review { font-size: 11px; color: var(--text-sm); margin-top: 2px; }
.sim-btn {
  display: block; text-align: center; margin-top: 10px; padding: 8px 0;
  background: var(--brand); color: #fff !important; border-radius: var(--r-sm);
  text-decoration: none; font-size: 12px; font-weight: 700;
  transition: background-color var(--ease), transform var(--ease);
}
.sim-btn:hover { background-color: var(--brand-dk); transform: translateY(-1px); }

/* ── サイドバー ─────────────────────────────── */
[data-testid="stSidebar"] { background: #f7f6f1 !important; border-right: 1px solid var(--border); }
.sb-brand {
  background: linear-gradient(135deg, #2e4d08 0%, #4d7c0f 55%, #84a98c 100%);
  border-radius: var(--r-md); padding: 20px; color: #fff; margin: 0 0 18px; text-align: center;
  box-shadow: 0 6px 22px rgba(77,124,15,.22); position: relative; overflow: hidden;
}
.sb-brand::after {
  content: ''; position: absolute; top: -30%; right: -15%; width: 160px; height: 160px;
  background: radial-gradient(circle, rgba(255,255,255,.10) 0%, transparent 60%);
  border-radius: 50%; pointer-events: none;
}
.sb-brand .sb-ic { font-size: 32px; line-height: 1; position: relative; }
.sb-brand .sb-tt { font-size: 17px; font-weight: 800; margin-top: 8px; position: relative; }
.sb-brand .sb-sub { font-size: 10px; opacity: .85; margin-top: 3px; letter-spacing: 2.5px; position: relative; }
.sb-h {
  font-size: 11px; font-weight: 800; color: var(--brand); letter-spacing: 1.5px;
  text-transform: uppercase; margin: 20px 0 10px; padding-bottom: 7px; border-bottom: 2px solid #eef3e3;
}
.sb-card {
  background: var(--card); border: 1px solid var(--border); border-left: 4px solid var(--brand);
  border-radius: var(--r-sm); padding: 13px 15px; font-size: 13px; color: var(--text-md); line-height: 1.65;
}
.sb-step { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 12px; }
.sb-step .n {
  flex: none; width: 26px; height: 26px; border-radius: 50%; background: var(--brand);
  color: #fff; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(77,124,15,.30);
}
.sb-step .tx { font-size: 13px; color: #3a3a36; line-height: 1.4; padding-top: 4px; }
.sb-link {
  display: block; text-align: center; margin-top: 10px; padding: 10px 12px;
  background: var(--text); color: #fff !important; border-radius: var(--r-sm);
  text-decoration: none; font-size: 13px; font-weight: 700;
  transition: background-color var(--ease);
}
.sb-link:hover { background-color: var(--brand); }

/* ── ダウンロードボタン ─────────────────────── */
[data-testid="stDownloadButton"] button {
  background: var(--text) !important; color: #fff !important;
  border: 0 !important; border-radius: var(--r-sm) !important;
  font-weight: 700 !important; padding: 11px 0 !important;
  box-shadow: 0 4px 14px rgba(43,43,40,.18) !important;
  transition: background-color var(--ease), transform var(--ease) !important;
}
[data-testid="stDownloadButton"] button:hover {
  background-color: var(--brand) !important; transform: translateY(-1px) !important;
}
[data-testid="stDownloadButton"] button p { font-size: 15px !important; font-weight: 700 !important; }

/* ── 完成予想図 説明ブロック ────────────────── */
.preview-desc {
  background: #f7f5ed; border-left: 4px solid var(--brand);
  border-radius: 0 var(--r-sm) var(--r-sm) 0;
  padding: 12px 16px; margin: 12px 0 4px;
  font-size: 14px; color: var(--text-md); line-height: 1.65;
}

/* ── セクション見出し ─────────────────────── */
.sec-hd {
  display: flex; align-items: center; gap: 10px;
  margin: 28px 0 16px; padding-bottom: 10px; border-bottom: 2px solid var(--border);
}
.sec-hd .ic { font-size: 20px; line-height: 1; }
.sec-hd .tx { font-size: 20px; font-weight: 700; color: var(--text); text-wrap: balance; }

/* ── 予算進捗バー ─────────────────────────── */
.budget-bar { height: 8px; background: var(--border); border-radius: 999px; overflow: hidden; margin: 14px 0 6px; }
.budget-bar-fill { height: 100%; border-radius: 999px; transition: width 0.5s cubic-bezier(0.4,0,0.2,1); }

/* ── メトリクスカード ─────────────────────── */
/* testid は Streamlit のバージョンで変わるため新旧両方を指定 */
[data-testid="metric-container"],
[data-testid="stMetric"] {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r-sm); padding: 16px 18px; box-shadow: var(--sh-sm);
}
[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }

/* ── Expander ─────────────────────────────── */
[data-testid="stExpander"] {
  border: 1px solid var(--border) !important; border-radius: var(--r-md) !important;
  margin-bottom: 10px !important; box-shadow: var(--sh-sm) !important;
  background: var(--card) !important; overflow: hidden !important;
  transition: box-shadow var(--ease), border-color var(--ease) !important;
}
[data-testid="stExpander"]:hover { box-shadow: var(--sh-md) !important; border-color: #c5d9a8 !important; }

/* ── 生成ボタン ─────────────────────────── */
/* testid は Streamlit のバージョンで変わるため新旧両方を指定 */
[data-testid="baseButton-primary"],
[data-testid="stBaseButton-primary"],
button[kind="primary"] {
  background: linear-gradient(135deg, var(--brand-dk) 0%, var(--brand) 60%, #6aa32a 100%) !important;
  border: none !important; border-radius: var(--r-sm) !important; font-weight: 800 !important;
  box-shadow: 0 4px 18px rgba(77,124,15,.30) !important;
  transition: transform var(--ease), box-shadow var(--ease) !important;
}
[data-testid="baseButton-primary"]:hover,
[data-testid="stBaseButton-primary"]:hover,
button[kind="primary"]:hover {
  transform: translateY(-2px) !important; box-shadow: 0 8px 28px rgba(77,124,15,.38) !important;
}

/* ── 空状態サンプルギャラリー ───────────────── */
.sample-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px; margin-top: 8px;
}
.sample-card {
  margin: 0; background: var(--card); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 10px; box-shadow: var(--sh-sm);
}
.sample-img {
  aspect-ratio: 16 / 10; border-radius: var(--r-sm);
  background-size: cover; background-position: center; background-color: #f1efe8;
}
.sample-card figcaption {
  font-size: 13px; font-weight: 700; color: var(--text-md);
  text-align: center; padding: 10px 0 4px;
}

/* ── モバイル対応 ─────────────────────────── */
@media (max-width: 640px) {
  .block-container { padding-top: 1.4rem; }
  .hero { padding: 22px 20px; }
  .hero h1 { font-size: 24px; }
  .hero p  { font-size: 14px; }
  .sim-card { width: calc(50% - 7px); }
}
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
            f'<div class="sim-img" role="img" aria-label="{name}" style="background-image:url(\'{img}\')"></div>'
            f'<span class="sim-badge"><span aria-hidden="true">🏷️ </span>{badge}</span>'
            f'<div class="sim-name">{name}</div>'
            f'<div class="sim-price">¥{p.price:,}</div>'
            f'{review}'
            f'<a class="sim-btn" href="{url}" target="_blank" rel="noopener noreferrer">{t(lang, "product_button")}</a>'
            f'</div>'
        )
    return f'<div class="sim-row">{"".join(cards)}</div>'


_ASSET_DIR = Path(__file__).parent / "assets"


@st.cache_data
def _sample_cards() -> list[tuple[str, str]]:
    """空状態ギャラリー用の (画像data URI, i18nキー) を返す。画像が無い環境では空リスト。"""
    cards = []
    for fname, key in (("preview_living.jpg", "sample_living"), ("preview_bedroom.jpg", "sample_bedroom")):
        path = _ASSET_DIR / fname
        if path.exists():
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            cards.append((f"data:image/jpeg;base64,{b64}", key))
    return cards


def _set_flash(level: str, message: str) -> None:
    """rerun をまたいで一度だけ表示するメッセージ（"success"/"warning"等）を記録する。"""
    st.session_state.flash = (level, message)


def _room_image_prompt() -> str:
    """完成予想図用の英語プロンプトを返す。

    生成時に保存した「全アイテムを配置した部屋全体」の room_image_prompt を優先し、
    無い場合（旧形式のセッション）は先頭アイテムの image_prompt にフォールバックする。
    """
    ctx = st.session_state.gen_ctx or {}
    items = st.session_state.coord_items or []
    fallback = items[0].get("image_prompt", "") if items else ""
    return ctx.get("room_image_prompt") or fallback


def _regenerate_item(idx: int, lang: str, regen_image: bool = False) -> None:
    """提案リストの idx 番目だけを、別アイテムに差し替えて再描画する。

    生成時に保存した gen_ctx（同じ間取り・予算・テイスト・手持ち家具）だけを使い、
    既存アイテムと重複しない代替を1件だけ生成して該当インデックスを書き換える。
    regen_image=True のときは「差し替え後の部屋全体」の room_image_prompt で完成予想図も
    作り直す（gpt-image-1 の追加課金）。結果はフラッシュメッセージで通知する。
    """
    items_now = st.session_state.coord_items or []
    ctx = st.session_state.gen_ctx
    if idx >= len(items_now) or not ctx:
        return  # 想定外の状態。何もせず通常の再描画に任せる

    target = items_now[idx]
    other_names = [it["item_name"] for j, it in enumerate(items_now) if j != idx]

    with st.spinner(t(lang, "spinner_regen")):
        try:
            new_item, new_room_prompt = OpenAICoordinateGenerator(OPENAI_KEY).regenerate_item(
                ctx["room_prompt"],
                ctx["budget"],
                ctx["taste"],
                ctx["language_name"],
                target_name=target["item_name"],
                other_names=other_names,
                slot_budget=int(target.get("price", 0)),
                owned_items=ctx.get("owned_items", ""),
            )
        except Exception as e:
            _set_flash("warning", t(lang, "warn_regen", e=e))
            st.rerun()

        # 古いアイテムのおすすめ商品を破棄し、該当枠だけ差し替える
        st.session_state.shopping_results.pop(target["item_name"], None)
        st.session_state.coord_items[idx] = new_item
        if new_room_prompt:
            # 以後のプレビュー更新が「差し替え後の部屋」で行われるよう上書きする
            ctx["room_image_prompt"] = new_room_prompt

        # 差し替えた新アイテムのおすすめ商品だけ再検索（失敗しても無視）
        if (RAKUTEN_APP_ID and RAKUTEN_ACCESS_KEY) or YAHOO_APP_ID:
            try:
                st.session_state.shopping_results.update(
                    search_all_items(
                        [new_item],
                        rakuten_id=RAKUTEN_APP_ID,
                        rakuten_access_key=RAKUTEN_ACCESS_KEY,
                        rakuten_origin=RAKUTEN_ORIGIN,
                        yahoo_id=YAHOO_APP_ID,
                    )
                )
            except Exception:
                pass

    # オプション：差し替え後の部屋全体の room_image_prompt で完成予想図も作り直す
    if regen_image:
        with st.spinner(t(lang, "spinner_image")):
            try:
                st.session_state.room_image = OpenAIImageGenerator(OPENAI_KEY).generate(
                    _room_image_prompt(),
                    reference_image=st.session_state.room_photo,
                )
            except Exception as e:
                # アイテム差し替えは成功済み。画像だけ失敗した旨を残す
                _set_flash("warning", t(lang, "warn_image", e=e))
                st.rerun()

    _set_flash("success", t(lang, "regen_done", name=new_item["item_name"]))
    st.rerun()


def _update_preview(lang: str) -> None:
    """部屋全体の room_image_prompt で完成予想図だけを単発で作り直す（追加課金）。"""
    prompt = _room_image_prompt()
    if not prompt:
        return
    with st.spinner(t(lang, "spinner_image")):
        try:
            st.session_state.room_image = OpenAIImageGenerator(OPENAI_KEY).generate(
                prompt,
                reference_image=st.session_state.room_photo,
            )
            _set_flash("success", t(lang, "preview_updated"))
        except Exception as e:
            _set_flash("warning", t(lang, "warn_image", e=e))
    st.rerun()


OPENAI_KEY = _get_secret("OPENAI_API_KEY")
RAKUTEN_APP_ID = _get_secret("RAKUTEN_APP_ID")
RAKUTEN_ACCESS_KEY = _get_secret("RAKUTEN_ACCESS_KEY")
RAKUTEN_ORIGIN = _get_secret("RAKUTEN_ORIGIN")
YAHOO_APP_ID = _get_secret("YAHOO_APP_ID")

# --- サイドバー：ブランドカード + 言語選択（最初に決定） ---
PRESENTATION_URL = "https://emuzu-morishita.github.io/ai-interior-app/presentation.html"

st.sidebar.markdown(
    '<div class="sb-brand"><div class="sb-ic" aria-hidden="true">🛋️</div>'
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
    f'<div class="hero"><h1><span aria-hidden="true">🛋️</span> AI Interior Coordinator</h1>'
    f'<p>{html_lib.escape(t(lang, "caption"))}</p></div>',
    unsafe_allow_html=True,
)

# --- セッション状態の初期化（st.stop() より先に必ず実行） ---
if "coord_items" not in st.session_state:
    st.session_state.coord_items = None
if "shopping_results" not in st.session_state:
    st.session_state.shopping_results = {}
if "room_image" not in st.session_state:
    st.session_state.room_image = None
if "error" not in st.session_state:
    st.session_state.error = None
if "room_photo" not in st.session_state:
    st.session_state.room_photo = None
if "gen_ctx" not in st.session_state:
    st.session_state.gen_ctx = None
if "flash" not in st.session_state:
    st.session_state.flash = None

if not OPENAI_KEY:
    st.error(t(lang, "err_no_openai"))
    st.stop()

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
        f'<a class="sb-link" href="{PRESENTATION_URL}" target="_blank" rel="noopener noreferrer">'
        f'<span aria-hidden="true">📊 </span>{html_lib.escape(t(lang, "presentation_link"))}</a>',
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

# 言語切替時は手持ち家具の選択をリセット（プリセットが言語別のため）
if st.session_state.get("prev_lang") != lang:
    st.session_state.pop("owned_ms", None)
    st.session_state.prev_lang = lang

# --- 詳細設定（任意）：現在の部屋写真アップロード + 手持ち家具の除外 ---
with st.expander(f"🛠️ {t(lang, 'advanced_options')}", expanded=False):
    adv_l, adv_r = st.columns([1, 1])
    with adv_l:
        photo_file = st.file_uploader(
            t(lang, "upload_photo_label"),
            type=["png", "jpg", "jpeg", "webp"],
            help=t(lang, "upload_photo_help"),
        )
        if photo_file is not None:
            st.image(photo_file, width="stretch")
            st.caption(t(lang, "photo_uploaded_caption"))
    with adv_r:
        owned_input = st.multiselect(
            t(lang, "owned_items_label"),
            options=i18n.OWNED_PRESETS[lang],
            default=[],
            key="owned_ms",  # 言語切替時にリセットするためのキー
            accept_new_options=True,  # プリセット選択 + 自由入力での追加に対応
            placeholder=t(lang, "owned_items_placeholder"),
            help=t(lang, "owned_items_help"),
        )

room_prompt = i18n.ROOM_SIZE_PROMPT[room_idx]
language_name = i18n.LANGUAGE_NAMES[lang]

if st.button(t(lang, "generate_btn"), type="primary", width="stretch"):
    # ボタンを押した瞬間に前回の結果・エラーをクリア
    st.session_state.coord_items = None
    st.session_state.shopping_results = {}
    st.session_state.room_image = None
    st.session_state.error = None

    # 手持ち家具（提案・予算から除外する対象）。マルチセレクトのリストを文字列化
    owned_items = ", ".join(owned_input) if owned_input else ""

    # アップロードされた現在の部屋写真を PIL 化して保持（Img2Img の参照画像）
    room_photo = None
    if photo_file is not None:
        try:
            room_photo = Image.open(photo_file).convert("RGB")
        except Exception:
            room_photo = None
    st.session_state.room_photo = room_photo

    # 個別再生成・結果表示・レポートで同じ条件を使い回せるよう、生成時のコンテキストを保存
    st.session_state.gen_ctx = {
        "room_prompt": room_prompt,
        "room_idx": room_idx,
        "budget": budget,
        "taste": taste,
        "language_name": language_name,
        "owned_items": owned_items,
    }

    # --- 生成パイプライン（st.status でステップ形式に進捗を可視化） ---
    shopping_enabled = (RAKUTEN_APP_ID and RAKUTEN_ACCESS_KEY) or YAHOO_APP_ID
    with st.status(t(lang, "status_running"), expanded=True) as status:
        # 1. コーディネート生成（ここが成否の分かれ目）
        st.write(f"📐 {t(lang, 'spinner_coordinate')}")
        try:
            result = OpenAICoordinateGenerator(OPENAI_KEY).generate(
                room_prompt, budget, taste, language_name, owned_items
            )
            st.session_state.coord_items = result["items"]
            # 全アイテムを配置した部屋全体の画像プロンプト（プレビュー更新でも使う）
            st.session_state.gen_ctx["room_image_prompt"] = result.get("room_image_prompt", "")
        except Exception as e:
            st.session_state.error = t(lang, "err_coordinate", e=e)

        # 2+3. 商品検索と画像生成は互いに独立なので並列実行し、待ち時間を短縮する。
        #      いずれも失敗は警告のみ（graceful degradation）でコーディネート提案は表示する。
        if st.session_state.coord_items:
            with ThreadPoolExecutor(max_workers=2) as pool:
                shop_future = None
                if shopping_enabled:
                    st.write(f"🛍️ {t(lang, 'spinner_shopping')}")
                    shop_future = pool.submit(
                        search_all_items,
                        st.session_state.coord_items,
                        rakuten_id=RAKUTEN_APP_ID,
                        rakuten_access_key=RAKUTEN_ACCESS_KEY,
                        rakuten_origin=RAKUTEN_ORIGIN,
                        yahoo_id=YAHOO_APP_ID,
                    )
                st.write(f"🖼️ {t(lang, 'spinner_image')}")
                image_future = pool.submit(
                    OpenAIImageGenerator(OPENAI_KEY).generate,
                    _room_image_prompt(),
                    reference_image=st.session_state.room_photo,
                )
                if shop_future is not None:
                    try:
                        st.session_state.shopping_results = shop_future.result()
                    except Exception as e:
                        st.warning(t(lang, "warn_shopping", e=e))
                try:
                    st.session_state.room_image = image_future.result()
                except Exception as e:
                    st.warning(t(lang, "warn_image", e=e))

        # 完了状態を更新（コーディネートが生成できていれば complete、できなければ error）
        if st.session_state.coord_items:
            status.update(label=t(lang, "status_done"), state="complete", expanded=False)
        else:
            status.update(label=t(lang, "status_error"), state="error", expanded=True)

# --- エラー表示 ---
if st.session_state.error:
    st.error(st.session_state.error)

# --- フラッシュメッセージ（再生成などの結果。rerunをまたいで一度だけ表示） ---
if st.session_state.flash:
    _flash_level, _flash_msg = st.session_state.flash
    if _flash_level == "success":
        st.toast(_flash_msg, icon="✅")  # 成功通知はレイアウトを押し下げないトーストで
    else:
        getattr(st, _flash_level)(_flash_msg)
    st.session_state.flash = None

# --- 結果表示 ---
if st.session_state.coord_items:
    items = st.session_state.coord_items
    shopping_results = st.session_state.shopping_results

    # 生成後に入力ウィジェットを動かしても表示・レポートが狂わないよう、
    # 金額計算と提案条件は「生成時の条件（gen_ctx）」を基準にする
    ctx = st.session_state.gen_ctx or {}
    gen_budget = ctx.get("budget", budget)
    gen_taste = ctx.get("taste", taste)
    gen_room_idx = ctx.get("room_idx", room_idx)

    total_price = sum(item["price"] for item in items)
    remaining = gen_budget - total_price
    over_budget = remaining < 0

    st.markdown("---")

    # 1. 完成予想図（一番上）＋ 単発「プレビューを更新」ボタン
    st.markdown(
        f'<div class="sec-hd"><span class="ic" aria-hidden="true">🖼️</span>'
        f'<span class="tx">{html_lib.escape(t(lang, "preview_header"))}</span></div>',
        unsafe_allow_html=True,
    )
    if st.session_state.room_image:
        st.image(st.session_state.room_image, width="stretch")
        st.markdown(
            f'<div class="preview-desc"><span aria-hidden="true">💡 </span>{html_lib.escape(t(lang, "preview_caption"))}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption(t(lang, "preview_none"))
    _, pv_r = st.columns([3, 1])
    with pv_r:
        if st.button(t(lang, "update_preview_btn"), key="update_preview", width="stretch"):
            _update_preview(lang)

    # 2. 提案アイテム一覧
    st.markdown(
        f'<div class="sec-hd"><span class="ic" aria-hidden="true">🛋️</span>'
        f'<span class="tx">{html_lib.escape(t(lang, "items_header"))}</span></div>',
        unsafe_allow_html=True,
    )
    regen_with_image = st.toggle(
        t(lang, "regen_with_image_label"),
        value=False,
        key="regen_with_image",
        help=t(lang, "regen_with_image_help"),
    )
    for i, item in enumerate(items, 1):
        idx = i - 1
        with st.expander(f"{i}. {item['item_name']} — ¥{item['price']:,}", expanded=True):
            head_l, head_r = st.columns([3, 1])
            with head_r:
                regen_clicked = st.button(
                    t(lang, "regen_item_btn"),
                    key=f"regen_{idx}",
                    width="stretch",
                )
            with head_l:
                st.write(item["reason"])
            if item.get("placement"):
                st.info(f"📐 **{t(lang, 'placement_label')}** {item['placement']}")
            products = shopping_results.get(item["item_name"], [])
            if products:
                st.markdown(f"**{t(lang, 'recommend_header')}**")
                st.markdown(_render_products(products, lang), unsafe_allow_html=True)
            elif (RAKUTEN_APP_ID and RAKUTEN_ACCESS_KEY) or YAHOO_APP_ID:
                st.caption(t(lang, "no_products"))

            if regen_clicked:
                _regenerate_item(idx, lang, regen_image=regen_with_image)

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
    pct = min(100, int(total_price / gen_budget * 100))
    bar_color = "#e74c3c" if over_budget else "var(--brand)"
    st.markdown(
        f'<div class="budget-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{pct}">'
        f'<div class="budget-bar-fill" style="width:{pct}%;background:{bar_color}"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if over_budget:
        st.warning(t(lang, "warn_over", amount=abs(remaining)))

    st.markdown(
        f'<div class="sec-hd"><span class="ic" aria-hidden="true">📊</span>'
        f'<span class="tx">{html_lib.escape(t(lang, "budget_breakdown"))}</span></div>',
        unsafe_allow_html=True,
    )
    chart_data = pd.DataFrame({
        t(lang, "chart_item"): [item["item_name"] for item in items],
        t(lang, "chart_price"): [item["price"] for item in items],
    })
    st.bar_chart(chart_data.set_index(t(lang, "chart_item")), color="#4d7c0f")

    # 4. 保存ボタン（最後）：リロードで消える前に好きな形式で手元に残す
    st.markdown("---")
    fmt = st.radio(t(lang, "save_format_label"), ["HTML", "PDF", "Excel"], horizontal=True)
    report_args = (items, shopping_results, st.session_state.room_image)
    report_kwargs = dict(
        lang=lang,
        room_label=i18n.ROOM_SIZE_LABELS[lang][gen_room_idx],
        taste=gen_taste,
        budget=gen_budget,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        owned_items=ctx.get("owned_items", ""),
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
            width="stretch",
        )
    except Exception as e:
        st.warning(t(lang, "warn_save", e=e))
    st.caption(t(lang, "download_caption"))

# --- 空状態（初回表示）：何が生成されるかが一目で分かるサンプルギャラリー ---
elif not st.session_state.error:
    _samples = _sample_cards()
    if _samples:
        st.markdown(
            f'<div class="sec-hd"><span class="ic" aria-hidden="true">✨</span>'
            f'<span class="tx">{html_lib.escape(t(lang, "sample_header"))}</span></div>',
            unsafe_allow_html=True,
        )
        _cards_html = "".join(
            f'<figure class="sample-card">'
            f'<div class="sample-img" role="img" aria-label="{html_lib.escape(t(lang, key))}"'
            f' style="background-image:url(\'{uri}\')"></div>'
            f'<figcaption>{html_lib.escape(t(lang, key))}</figcaption></figure>'
            for uri, key in _samples
        )
        st.markdown(f'<div class="sample-grid">{_cards_html}</div>', unsafe_allow_html=True)
        st.caption(t(lang, "sample_note"))
