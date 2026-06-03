def build_coordinate_prompt(room_size: str, budget: int, taste: str) -> str:
    return f"""
あなたはプロのインテリアコーディネーターです。
以下の条件に合わせた家具・インテリアの提案を3〜5アイテム、必ず指定されたJSONフォーマットのみで出力してください。

【条件】
- 広さ: {room_size}
- 予算合計: {budget}円（全アイテムの合計金額が予算内に収まるよう配分すること）
- テイスト: {taste}

【予算が低い場合のルール】
予算が20,000円未満の場合は、大型家具の提案は避け、照明・クッション・ラグ・観葉植物など
小物・アクセントアイテムで部屋の質感を上げる代替案を優先してください。

【image_promptの厳守事項】
各アイテムのimage_promptには、そのアイテムが実際に配置された「部屋全体のレイアウトと
空間の広がりがすべて見渡せる画像」を生成するための英語プロンプトを書いてください。
必ず以下のキーワードを複数含めること:
"Ultra-wide angle shot", "Full room view", "Showcasing the entire room layout", "Architectural photography style"
""".strip()


ITEM_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "item_name": {"type": "string", "description": "家具・小物の名前"},
        "price": {"type": "integer", "description": "概算金額（円）"},
        "reason": {"type": "string", "description": "選定した理由"},
        "image_prompt": {"type": "string", "description": "Stable Diffusion / DALL-E用の高精細な英語画像生成プロンプト"},
    },
    "required": ["item_name", "price", "reason", "image_prompt"],
    "additionalProperties": False,
}

RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": ITEM_JSON_SCHEMA,
            "description": "提案する家具・インテリアアイテムのリスト",
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}
