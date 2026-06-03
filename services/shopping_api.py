import requests
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

_RAKUTEN_SEARCH_URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"


@dataclass
class ShoppingItem:
    name: str
    price: int
    url: str
    image_url: str
    shop_name: str
    review_average: float
    review_count: int
    source: str = ""  # "楽天市場" / "Yahoo!ショッピング"


def search_rakuten(app_id: str, keyword: str, suggested_price: int, hits: int = 3) -> list[ShoppingItem]:
    """楽天市場でキーワード検索し、提案価格に近い商品を返す。"""
    params = {
        "applicationId": app_id,
        "keyword": keyword,
        "hits": 9,  # 多めに取得して価格でソート後に絞る
        "minPrice": max(100, int(suggested_price * 0.3)),
        "maxPrice": int(suggested_price * 2.5),
        "sort": "+itemPrice",
        "imageFlag": 1,
        "format": "json",
        "formatVersion": 2,
    }

    try:
        response = requests.get(_RAKUTEN_SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"楽天API 通信エラー: {e}") from e

    raw_items = response.json().get("Items", [])

    results = []
    for item in raw_items[:hits]:
        images = item.get("mediumImageUrls", [])
        image_url = images[0]["imageUrl"].replace("?_ex=128x128", "?_ex=240x240") if images else ""
        results.append(ShoppingItem(
            name=item.get("itemName", ""),
            price=int(item.get("itemPrice", 0)),
            url=item.get("itemUrl", ""),
            image_url=image_url,
            shop_name=item.get("shopName", ""),
            review_average=float(item.get("reviewAverage", 0)),
            review_count=int(item.get("reviewCount", 0)),
            source="楽天市場",
        ))

    return results


def search_all_items(
    items: list[dict],
    rakuten_id: str = "",
    yahoo_id: str = "",
    hits_per_provider: int = 2,
    max_per_item: int = 4,
) -> dict[str, list[ShoppingItem]]:
    """全アイテムを楽天・Yahoo!で並列検索し、{item_name: [ShoppingItem]} を返す。

    各アイテムごとに両プロバイダーの結果を結合し、価格の安い順に max_per_item 件まで絞る。
    """
    # 遅延importで循環参照を回避（yahoo側が ShoppingItem を参照するため）
    from services.yahoo_shopping_api import search_yahoo

    def _fetch(item: dict) -> tuple[str, list[ShoppingItem]]:
        name = item["item_name"]
        price = item["price"]
        products: list[ShoppingItem] = []
        if rakuten_id:
            try:
                products += search_rakuten(rakuten_id, name, price, hits=hits_per_provider)
            except RuntimeError:
                pass
        if yahoo_id:
            try:
                products += search_yahoo(yahoo_id, name, price, hits=hits_per_provider)
            except RuntimeError:
                pass
        products.sort(key=lambda p: p.price)
        return name, products[:max_per_item]

    results: dict[str, list[ShoppingItem]] = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch, item): item for item in items}
        for future in as_completed(futures):
            name, products = future.result()
            results[name] = products

    return results
