"""API課金なしで全フローを検証するスモークテスト。

OpenAI（テキスト・画像）と楽天/Yahoo!検索をフェイクに差し替えて、
生成パイプライン → 結果表示 → レポート3形式 → 個別再生成 → プレビュー更新
までを Streamlit AppTest で一気に通す。実行方法:

    venv\\Scripts\\python.exe tests\\smoke_test.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # リポジトリ直下を import 可能に
os.chdir(Path(__file__).resolve().parents[1])  # assets/ 等の相対参照のため

os.environ.setdefault("OPENAI_API_KEY", "dummy-key")
os.environ.setdefault("YAHOO_APP_ID", "dummy-yahoo")

from PIL import Image

import services.openai_service as osvc
import services.openai_image_service as isvc
import services.shopping_api as shop

# --- i18n: 4言語のキー集合が一致していること（1言語でも欠けるとキー名がそのまま表示される） ---
from services.i18n import TRANSLATIONS

_base = set(TRANSLATIONS["ja"].keys())
for _lang, _table in TRANSLATIONS.items():
    assert set(_table.keys()) == _base, (
        f"i18n キー不一致 ({_lang}): "
        f"missing={sorted(_base - set(_table))} extra={sorted(set(_table) - _base)}"
    )
print(f"[0] i18n 全{len(TRANSLATIONS)}言語キーパリティ OK")

# --- フェイクプロバイダー ---
ITEMS = [
    {
        "item_name": f"テストアイテム{i}",
        "price": 10000 * i,
        "reason": f"理由{i}",
        "placement": f"南向きの窓際に配置{i}",
        "search_keyword": "ソファ 北欧",
    }
    for i in (1, 2, 3)
]

calls = {"image_prompts": [], "search_keywords": []}


class FakeGen:
    def __init__(self, *a, **k):
        pass

    def generate(self, *a, **k):
        return {"items": ITEMS, "room_image_prompt": "Ultra-wide angle shot, full room"}

    def regenerate_item(self, *a, **k):
        new_item = {
            "item_name": "差し替えアイテム",
            "price": 12345,
            "reason": "新しい理由",
            "placement": "北東の壁面に設置",
            "search_keyword": "ラグ 洗える",
        }
        return new_item, "Updated ultra-wide room prompt"


class FakeImg:
    def __init__(self, *a, **k):
        pass

    def generate(self, prompt, reference_image=None):
        calls["image_prompts"].append(prompt)
        return Image.new("RGB", (1536, 1024), "#cccccc")


def fake_search(items, **kwargs):
    for it in items:
        calls["search_keywords"].append(it.get("search_keyword") or it["item_name"])
    return {
        it["item_name"]: [
            shop.ShoppingItem(
                name="フェイク商品",
                price=9999,
                url="https://example.com/item",
                image_url="",
                shop_name="テスト店",
                review_average=4.5,
                review_count=12,
                source="楽天市場",
            )
        ]
        for it in items
    }


osvc.OpenAICoordinateGenerator = FakeGen
isvc.OpenAIImageGenerator = FakeImg
shop.search_all_items = fake_search

from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py", default_timeout=120)
at.run()
assert not at.exception, f"初回表示で例外: {[e.value for e in at.exception]}"
md_all = " ".join(str(m.value) for m in at.markdown)
assert "sample-grid" in md_all, "空状態サンプルギャラリーが表示されていない"
print("[1] 初回表示 OK（空状態ギャラリーあり）")

# 生成ボタン（初回表示で唯一の st.button）を押す
assert len(at.button) == 1, f"初回表示のボタン数が想定外: {[b.label for b in at.button]}"
at.button[0].click()
at.run()
assert not at.exception, f"生成フローで例外: {[e.value for e in at.exception]}"
assert at.session_state["coord_items"] == ITEMS, "coord_items が想定と異なる"
assert at.session_state["gen_ctx"]["room_image_prompt"] == "Ultra-wide angle shot, full room"
assert at.session_state["gen_ctx"]["room_idx"] == 0
assert at.session_state["room_image"] is not None, "完成予想図が生成されていない"
assert calls["image_prompts"] == ["Ultra-wide angle shot, full room"], (
    "画像生成に room_image_prompt が使われていない"
)
assert len(at.session_state["shopping_results"]) == 3, "商品検索結果が3件分ない"
assert set(calls["search_keywords"]) == {"ソファ 北欧"}, "検索に search_keyword が使われていない"
print("[2] 生成パイプライン OK（room_image_prompt / search_keyword / 並列実行）")

# 結果画面: ダウンロードボタンが出ている＝選択形式のビルダーが例外なく完走した証拠
assert len(at.get("download_button")) == 1, "ダウンロードボタンが表示されていない"
print("[3] 結果表示 + レポートビルダー OK")

# レポート3形式を全言語で直接ビルドして検証（placement・フォント・形式が壊れていないこと）
from services.report import build_html_report, build_pdf_report, build_excel_report
from services.i18n import ROOM_SIZE_LABELS

shopping = fake_search(ITEMS)
room_img = Image.new("RGB", (1536, 1024), "#dddddd")
for _lng in TRANSLATIONS.keys():
    kwargs = dict(lang=_lng, room_label=ROOM_SIZE_LABELS[_lng][0], taste="北欧モダン",
                  budget=50000, generated_at="2026-06-12 12:00", owned_items="ソファ")
    html_out = build_html_report(ITEMS, shopping, room_img, **kwargs)
    pdf_out = build_pdf_report(ITEMS, shopping, room_img, **kwargs)
    xlsx_out = build_excel_report(ITEMS, shopping, room_img, **kwargs)
    if _lng == "ja":
        assert "南向きの窓際に配置1" in html_out, "HTMLレポートに placement が無い"
    assert pdf_out[:4] == b"%PDF", f"PDFが壊れている ({_lng})"
    assert xlsx_out[:2] == b"PK", f"Excelが壊れている ({_lng})"
print(f"[4] レポート3形式 × 全{len(TRANSLATIONS)}言語（placement 入り）OK")

# 個別再生成（regen_0）→ 差し替え + room_image_prompt 更新 + 商品再検索の確認
at.button(key="regen_0").click()
at.run()
assert not at.exception, f"再生成で例外: {[e.value for e in at.exception]}"
assert at.session_state["coord_items"][0]["item_name"] == "差し替えアイテム", "アイテムが差し替わっていない"
assert at.session_state["gen_ctx"]["room_image_prompt"] == "Updated ultra-wide room prompt", (
    "再生成後の room_image_prompt が更新されていない"
)
assert "差し替えアイテム" in at.session_state["shopping_results"], "差し替え後の商品再検索がされていない"
print("[5] 個別再生成 OK（room_image_prompt 引き継ぎ・商品再検索）")

# プレビュー更新ボタン → 最新の room_image_prompt が使われること
at.button(key="update_preview").click()
at.run()
assert not at.exception, f"プレビュー更新で例外: {[e.value for e in at.exception]}"
assert calls["image_prompts"][-1] == "Updated ultra-wide room prompt", (
    "プレビュー更新に最新の room_image_prompt が使われていない"
)
print("[6] プレビュー更新 OK")

print("ALL CHECKS PASSED")
