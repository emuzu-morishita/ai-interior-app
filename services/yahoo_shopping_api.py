import requests

from services.shopping_api import ShoppingItem

_YAHOO_SEARCH_URL = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"


def search_yahoo(app_id: str, keyword: str, suggested_price: int, hits: int = 3) -> list[ShoppingItem]:
    """Yahoo!ショッピングでキーワード検索し、提案価格に近い商品を返す。"""
    params = {
        "appid": app_id,
        "query": keyword,
        "results": 10,  # 多めに取得して価格でソート後に絞る
        "price_from": max(100, int(suggested_price * 0.3)),
        "price_to": int(suggested_price * 2.5),
        "sort": "+price",
        "in_stock": "true",
    }

    try:
        response = requests.get(_YAHOO_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Yahoo!ショッピングAPI 通信エラー: {e}") from e

    raw_items = response.json().get("hits", [])

    results = []
    for item in raw_items[:hits]:
        image = item.get("image", {}) or {}
        review = item.get("review", {}) or {}
        seller = item.get("seller", {}) or {}
        results.append(ShoppingItem(
            name=item.get("name", ""),
            price=int(item.get("price", 0)),
            url=item.get("url", ""),
            image_url=image.get("medium", "") or image.get("small", ""),
            shop_name=seller.get("name", ""),
            review_average=float(review.get("rate", 0) or 0),
            review_count=int(review.get("count", 0) or 0),
            source="Yahoo!ショッピング",
        ))

    return results
