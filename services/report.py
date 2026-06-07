"""生成結果（提案アイテム・おすすめ商品・完成予想図）を、画像を base64 で
埋め込んだ単一HTMLファイルにまとめるモジュール。

ブラウザのリロードで st.session_state が消えても手元に残せるよう、
外部リソースに依存しない自己完結したHTMLを生成する。
"""
import base64
import io
import html as html_lib

from services.i18n import t


def _image_data_uri(image) -> str:
    """PIL Image を PNG の data URI 文字列に変換する。"""
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _product_cards(products, lang: str) -> str:
    """おすすめ商品を固定サイズのHTMLカード列としてレンダリングする。"""
    cards = []
    for p in products:
        name = html_lib.escape(p.name[:60] + ("…" if len(p.name) > 60 else ""))
        url = html_lib.escape(p.url or "", quote=True)
        img = html_lib.escape(p.image_url or "", quote=True)
        src = html_lib.escape(p.source)
        img_div = (
            f'<span class="p-img" style="background-image:url(\'{img}\')"></span>'
            if img else '<span class="p-img"></span>'
        )
        review = ""
        if p.review_average > 0:
            review = f'<span class="p-review">{t(lang, "review_fmt", avg=p.review_average, count=p.review_count)}</span>'
        cards.append(
            f'<a class="p-card" href="{url}" target="_blank" rel="noopener">'
            f'{img_div}'
            f'<span class="p-badge">🏷️ {src}</span>'
            f'<span class="p-name">{name}</span>'
            f'<span class="p-price">¥{p.price:,}</span>'
            f'{review}'
            f'</a>'
        )
    return f'<div class="p-row">{"".join(cards)}</div>'


def build_html_report(
    items,
    shopping_results,
    room_image,
    *,
    lang: str,
    room_label: str,
    taste: str,
    budget: int,
    generated_at: str,
) -> str:
    """生成結果一式を単一HTMLファイル（画像埋め込み）にまとめて返す。"""
    total = sum(it["price"] for it in items)

    # --- 完成予想図 ---
    image_block = ""
    if room_image is not None:
        image_block = (
            f'<section class="card preview">'
            f'<h2>🖼️ {html_lib.escape(t(lang, "preview_header"))}</h2>'
            f'<img src="{_image_data_uri(room_image)}" alt="room preview">'
            f'<p class="cap">{html_lib.escape(t(lang, "preview_caption"))}</p>'
            f'</section>'
        )

    # --- 提案条件 ---
    meta_rows = "".join(
        f'<div class="meta-row"><span class="k">{html_lib.escape(k)}</span>'
        f'<span class="v">{html_lib.escape(v)}</span></div>'
        for k, v in (
            (t(lang, "room_size_label"), room_label),
            (t(lang, "taste_label"), taste),
            (t(lang, "budget_metric"), f"¥{budget:,}"),
            (t(lang, "m_total"), f"¥{total:,}"),
            (t(lang, "report_generated"), generated_at),
        )
    )

    # --- アイテム一覧 ---
    item_blocks = []
    for i, it in enumerate(items, 1):
        name = html_lib.escape(it["item_name"])
        reason = html_lib.escape(it["reason"])
        products = shopping_results.get(it["item_name"], [])
        rec_block = ""
        if products:
            rec_block = (
                f'<div class="rec-h">{html_lib.escape(t(lang, "recommend_header"))}</div>'
                f'{_product_cards(products, lang)}'
            )
        item_blocks.append(
            f'<div class="item">'
            f'<div class="item-head">'
            f'<span class="item-no">{i}</span>'
            f'<span class="item-name">{name}</span>'
            f'<span class="item-price">¥{it["price"]:,}</span>'
            f'</div>'
            f'<p class="item-reason">{reason}</p>'
            f'{rec_block}'
            f'</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="{html_lib.escape(lang, quote=True)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Interior Coordinator</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; padding: 24px; background: #fbfaf7; color: #2b2b28;
  font-family: -apple-system, "Segoe UI", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Microsoft YaHei", "Malgun Gothic", Meiryo, sans-serif; }}
.wrap {{ max-width: 880px; margin: 0 auto; }}
.hero {{ background: linear-gradient(120deg, #4d7c0f 0%, #84a98c 100%);
  border-radius: 22px; padding: 28px 34px; color: #fff; box-shadow: 0 10px 28px rgba(77,124,15,.2); }}
.hero h1 {{ margin: 0; font-size: 30px; font-weight: 800; }}
.hero p {{ margin: 8px 0 0; opacity: .93; font-size: 14px; }}
.card {{ background: #fff; border: 1px solid #e7e3d8; border-radius: 16px;
  padding: 20px 24px; margin-top: 18px; box-shadow: 0 2px 12px rgba(0,0,0,.04); }}
h2 {{ font-size: 18px; color: #4d7c0f; margin: 0 0 14px; }}
.meta-row {{ display: flex; justify-content: space-between; padding: 9px 0;
  border-bottom: 1px dashed #e7e3d8; font-size: 14px; }}
.meta-row:last-child {{ border-bottom: none; }}
.meta-row .k {{ color: #7a7468; }}
.meta-row .v {{ font-weight: 700; }}
.preview img {{ width: 100%; border-radius: 12px; display: block; }}
.preview .cap {{ font-size: 12px; color: #9a8f7d; margin: 8px 0 0; text-align: center; }}
.item {{ border-top: 1px solid #efece3; padding: 18px 0; }}
.item:first-of-type {{ border-top: none; }}
.item-head {{ display: flex; align-items: center; gap: 10px; }}
.item-no {{ flex: none; width: 26px; height: 26px; border-radius: 50%; background: #4d7c0f;
  color: #fff; font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: center; }}
.item-name {{ font-weight: 700; font-size: 16px; flex: 1; }}
.item-price {{ font-weight: 800; color: #4d7c0f; white-space: nowrap; }}
.item-reason {{ margin: 10px 0 0; font-size: 14px; line-height: 1.7; color: #4a4a44; }}
.rec-h {{ font-size: 12px; font-weight: 700; color: #4d7c0f; margin: 14px 0 9px; }}
.p-row {{ display: flex; flex-wrap: wrap; gap: 12px; }}
.p-card {{ width: 150px; border: 1px solid #e7e3d8; border-radius: 12px; padding: 9px;
  text-decoration: none; color: inherit; background: #fff; }}
.p-img {{ display: block; width: 100%; aspect-ratio: 1/1; border-radius: 8px; background: #f1efe8;
  background-size: cover; background-position: center; }}
.p-badge {{ display: inline-block; font-size: 10px; font-weight: 700; color: #4d7c0f;
  background: #eef3e3; border-radius: 6px; padding: 2px 7px; margin-top: 8px; }}
.p-name {{ display: block; font-size: 11px; line-height: 1.35; height: 30px; overflow: hidden; margin-top: 5px; color: #3a3a36; }}
.p-price {{ display: block; font-size: 15px; font-weight: 800; margin-top: 5px; }}
.p-review {{ display: block; font-size: 10px; color: #9a8f7d; margin-top: 2px; }}
footer {{ text-align: center; color: #9a8f7d; font-size: 11px; margin: 26px 0 6px; }}
</style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <h1>🛋️ AI Interior Coordinator</h1>
      <p>{html_lib.escape(t(lang, "caption"))}</p>
    </header>
    <section class="card">
      <h2>📋 {html_lib.escape(t(lang, "report_conditions"))}</h2>
      {meta_rows}
    </section>
    {image_block}
    <section class="card">
      <h2>🛋️ {html_lib.escape(t(lang, "items_header"))}</h2>
      {"".join(item_blocks)}
    </section>
    <footer>AI Interior Coordinator · {html_lib.escape(generated_at)}</footer>
  </div>
</body>
</html>"""
