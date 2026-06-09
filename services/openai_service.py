import json
from openai import OpenAI

from services.base import CoordinateGeneratorBase
from services.prompt import (
    build_coordinate_prompt,
    build_single_item_prompt,
    RESPONSE_JSON_SCHEMA,
)


class OpenAICoordinateGenerator(CoordinateGeneratorBase):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def _complete(self, prompt: str) -> list[dict]:
        """プロンプトを Structured Outputs で実行し、items 配列を返す共通処理。"""
        response = self._client.chat.completions.create(
            model=self._model,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "interior_coordinate",
                    "schema": RESPONSE_JSON_SCHEMA,
                    "strict": True,
                },
            },
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(response.choices[0].message.content)["items"]

    def generate(
        self,
        room_size: str,
        budget: int,
        taste: str,
        language: str = "Japanese",
        owned_items: str = "",
    ) -> list[dict]:
        return self._complete(
            build_coordinate_prompt(room_size, budget, taste, language, owned_items)
        )

    def regenerate_item(
        self,
        room_size: str,
        budget: int,
        taste: str,
        language: str = "Japanese",
        *,
        target_name: str,
        other_names: list[str],
        slot_budget: int,
        owned_items: str = "",
    ) -> dict:
        """提案リストのうち1アイテムだけを差し替える新しいアイテムを1件返す。"""
        items = self._complete(build_single_item_prompt(
            room_size, budget, taste, language,
            target_name=target_name,
            other_names=other_names,
            slot_budget=slot_budget,
            owned_items=owned_items,
        ))
        if not items:
            raise RuntimeError("再生成で有効なアイテムが返りませんでした。")
        return items[0]
