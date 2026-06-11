# 共通の出力ルール（通常生成・個別再生成で共用し、表現のブレを防ぐ）
def _language_rules(language: str) -> str:
    return f"""【出力言語の厳守事項】
item_name・reason・placement の各フィールドは、必ず {language} で記述してください。
ただし room_image_prompt は画像生成精度のため、言語設定にかかわらず必ず英語で記述すること。
search_keyword は日本のECサイト検索に使うため、言語設定にかかわらず必ず日本語で記述すること。"""


_PLACEMENT_RULES = """【placementの厳守事項】
placement には「部屋のどの位置にどの向きで置くか」を1〜2文で具体的かつ実用的に記述してください。
方角・窓・壁・動線との関係を含めて説明すること。
（例：「南向きの窓際に向けて斜め45度に配置し、自然光を取り込む」「北東の壁面に壁付けで設置し、通路幅を確保する」）"""


_SEARCH_KEYWORD_RULES = """【search_keywordの厳守事項】
search_keyword は日本のECサイト（楽天市場・Yahoo!ショッピング）での商品検索に使います。
出力言語にかかわらず必ず日本語で、「商品カテゴリ + 重要な特徴」を2〜3語、スペース区切りで
記述してください（例:「ソファ 2人掛け 北欧」「フロアランプ 木製」）。
ブランド名・色番号・寸法など細かすぎる修飾語は含めず、検索でヒットしやすい一般的な語を選ぶこと。"""


_ROOM_IMAGE_PROMPT_RULES = """【room_image_promptの厳守事項】
room_image_prompt には、提案した全アイテム（手持ち家具が指定されていればそれも含む）を
各 placement のとおりに配置した「部屋全体の完成予想図」を生成するための英語プロンプトを
書いてください。各アイテムの素材・色・互いの位置関係を具体的に描写し、
必ず以下のキーワードを複数含めること:
"Ultra-wide angle shot", "Full room view", "Showcasing the entire room layout", "Architectural photography style\""""


def _owned_items_block(owned_items: str) -> str:
    """「手持ち家具」を提案・予算から除外させるプロンプト断片を返す（空なら空文字）。"""
    owned = (owned_items or "").strip()
    if not owned:
        return ""
    return f"""
【すでに所有している家具・小物（提案・予算から必ず除外）】
ユーザーは以下をすでに所有しています。これらは新たに提案・購入リストに含めないでください。
ただし、これらが部屋に既にある前提で全体のレイアウトと image_prompt を構成すること。
{owned}
"""


def build_coordinate_prompt(
    room_size: str,
    budget: int,
    taste: str,
    language: str = "Japanese",
    owned_items: str = "",
) -> str:
    return f"""
あなたはプロのインテリアコーディネーターです。
以下の条件に合わせた家具・インテリアの提案を3〜5アイテム、必ず指定されたJSONフォーマットのみで出力してください。

【条件】
- 広さ: {room_size}
- 予算合計: {budget}円（全アイテムの合計金額が予算内に収まるよう配分すること）
- テイスト: {taste}
{_owned_items_block(owned_items)}
{_language_rules(language)}

【予算が低い場合のルール】
予算が20,000円未満の場合は、大型家具の提案は避け、照明・クッション・ラグ・観葉植物など
小物・アクセントアイテムで部屋の質感を上げる代替案を優先してください。

{_PLACEMENT_RULES}

{_SEARCH_KEYWORD_RULES}

{_ROOM_IMAGE_PROMPT_RULES}
""".strip()


def build_single_item_prompt(
    room_size: str,
    budget: int,
    taste: str,
    language: str = "Japanese",
    *,
    target_name: str,
    other_names: list[str],
    slot_budget: int,
    owned_items: str = "",
) -> str:
    """提案リストのうち1アイテムだけを差し替えるためのプロンプト。

    既存アイテムとの重複を避け、差し替え枠の目安予算に収まる新しいアイテムを
    「ちょうど1つ」返させる（items は要素1つの配列）。
    """
    others = "、".join(other_names) if other_names else "（なし）"
    return f"""
あなたはプロのインテリアコーディネーターです。
既存のインテリア提案のうち「1アイテムだけ」を、別の新しいアイテムに差し替えます。
差し替える新しいアイテムを「ちょうど1つだけ」提案し、必ず指定JSONフォーマット（items は要素1つだけの配列）で出力してください。

【部屋の条件】
- 広さ: {room_size}
- 全体テイスト: {taste}
- 全体予算の目安: {budget}円
- このアイテム枠の目安予算: 約{slot_budget}円（多少前後しても可）

【差し替え対象（ユーザーが気に入らなかったアイテム）】
- {target_name}
→ これとは異なる種類・形・素材の、新鮮な代替アイテムを提案すること。単なる色違いや同型の言い換えは禁止。

【すでに提案済みで、重複させてはいけないアイテム】
- {others}
{_owned_items_block(owned_items)}
{_language_rules(language)}

{_PLACEMENT_RULES}

{_SEARCH_KEYWORD_RULES}

{_ROOM_IMAGE_PROMPT_RULES}
※ room_image_prompt には「差し替え後の部屋全体」、つまり上記の既存アイテムと
新しいアイテムがすべて配置された部屋を描写すること。
""".strip()


ITEM_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "item_name": {"type": "string", "description": "家具・小物の名前"},
        "price": {"type": "integer", "description": "概算金額（円）"},
        "reason": {"type": "string", "description": "選定した理由"},
        "placement": {"type": "string", "description": "部屋のどの位置にどの向きで置くかの具体的な配置アドバイス（出力言語で記述）"},
        "search_keyword": {"type": "string", "description": "楽天市場・Yahoo!ショッピング検索用のシンプルな日本語キーワード（言語設定にかかわらず常に日本語。例: ソファ 2人掛け 北欧）"},
    },
    "required": ["item_name", "price", "reason", "placement", "search_keyword"],
    "additionalProperties": False,
}

RESPONSE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": ITEM_JSON_SCHEMA,
            "description": "提案する家具・インテリアアイテムのリスト",
        },
        "room_image_prompt": {
            "type": "string",
            "description": "全提案アイテムを placement どおりに配置した部屋全体の完成予想図を生成するための英語プロンプト（言語設定にかかわらず常に英語）",
        },
    },
    "required": ["items", "room_image_prompt"],
    "additionalProperties": False,
}
