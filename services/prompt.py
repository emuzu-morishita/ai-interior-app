def build_coordinate_prompt(room_size: str, budget: int, taste: str, language: str = "Japanese") -> str:
    return f"""
あなたはプロのインテリアコーディネーターです。
以下の条件に合わせた家具・インテリアの提案を3〜5アイテム、必ず指定されたJSONフォーマットのみで出力してください。

【条件】
- 広さ: {room_size}
- 予算合計: {budget}円（全アイテムの合計金額が予算内に収まるよう配分すること）
- テイスト: {taste}

【出力言語の厳守事項】
item_name・reason・placement の各フィールドは、必ず {language} で記述してください。
ただし image_prompt は画像生成精度のため、言語設定にかかわらず必ず英語で記述すること。

【予算が低い場合のルール】
予算が20,000円未満の場合は、大型家具の提案は避け、照明・クッション・ラグ・観葉植物など
小物・アクセントアイテムで部屋の質感を上げる代替案を優先してください。

【placementの厳守事項】
placement には「部屋のどの位置にどの向きで置くか」を1〜2文で具体的かつ実用的に記述してください。
方角・窓・壁・動線との関係を含めて説明すること。
（例：「南向きの窓際に向けて斜め45度に配置し、自然光を取り込む」「北東の壁面に壁付けで設置し、通路幅を確保する」）

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
        "placement": {"type": "string", "description": "部屋のどの位置にどの向きで置くかの具体的な配置アドバイス（出力言語で記述）"},
        "image_prompt": {"type": "string", "description": "画像生成用の高精細な英語プロンプト（言語設定にかかわらず常に英語）"},
    },
    "required": ["item_name", "price", "reason", "placement", "image_prompt"],
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
