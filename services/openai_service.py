import json
from openai import OpenAI

from services.base import CoordinateGeneratorBase
from services.prompt import build_coordinate_prompt, RESPONSE_JSON_SCHEMA


class OpenAICoordinateGenerator(CoordinateGeneratorBase):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, room_size: str, budget: int, taste: str, language: str = "Japanese") -> list[dict]:
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
            messages=[
                {"role": "user", "content": build_coordinate_prompt(room_size, budget, taste, language)}
            ],
        )
        return json.loads(response.choices[0].message.content)["items"]
