import requests
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

# 2026年2月の刷新後エンドポイント（旧 app.rakuten.co.jp/services/api/... は廃止）
_RAKUTEN_SEARCH_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"


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


def search_rakuten(
    app_id: str,
    access_key: str,
    origin: str,
    keyword: str,
    suggested_price: int,
    hits: int = 3,
) -> list[ShoppingItem]:
    """楽天市場（2026年新API）でキーワード検索し、提案価格に近い商品を返す。

    新APIは applicationId(UUID) と accessKey(pk_...) の両方、および
    登録済みドメインと一致する Origin/Referer ヘッダーを要求する。
    """
    params = {
        "applicationId": app_id,
        "accessKey": access_key,
        "keyword": keyword,
        "hits": hits,
        "minPrice": max(100, int(suggested_price * 0.3)),
        "maxPrice": int(suggested_price * 2.5),
        "sort": "+itemPrice",
        "imageFlag": 1,
        "format": "json",
        "formatVersion": 2,
    }
    headers = {}
    if origin:
        headers["Origin"] = origin
        headers["Referer"] = origin

    try:
        response = requests.get(_RAKUTEN_SEARCH_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"楽天API 通信エラー: {e}") from e

    raw_items = response.json().get("Items", [])

    results = []
    for item in raw_items[:hits]:
        # formatVersion=2 では mediumImageUrls はURL文字列のリスト
        images = item.get("mediumImageUrls", [])
        image_url = images[0].replace("?_ex=128x128", "?_ex=240x240") if images else ""
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
    rakuten_access_key: str = "",
    rakuten_origin: str = "",
    yahoo_id: str = "",
    hits_per_provider: int = 2,
    max_per_item: int = 4,
) -> dict[str, list[ShoppingItem]]:
    """全アイテムを楽天・Yahoo!で並列検索し、{item_name: [ShoppingItem]} を返す。

    各アイテムごとに両プロバイダーの結果を結合し、価格の安い順に max_per_item 件まで絞る。
    楽天は applicationId と accessKey の両方が揃っている場合のみ実行する。
    """
    # 遅延importで循環参照を回避（yahoo側が ShoppingItem を参照するため）
    from services.yahoo_shopping_api import search_yahoo

    rakuten_enabled = bool(rakuten_id and rakuten_access_key)

    def _fetch(item: dict) -> tuple[str, list[ShoppingItem]]:
        name = item["item_name"]
        price = item["price"]
        products: list[ShoppingItem] = []
        if rakuten_enabled:
            try:
                products += search_rakuten(
                    rakuten_id, rakuten_access_key, rakuten_origin, name, price, hits=hits_per_provider
                )
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
