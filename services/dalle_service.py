import requests
from PIL import Image
import io
from openai import OpenAI

from services.base import ImageGeneratorBase


class DallEImageGenerator(ImageGeneratorBase):
    def __init__(self, api_key: str, model: str = "dall-e-3"):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, prompt: str) -> Image.Image:
        response = self._client.images.generate(
            model=self._model,
            prompt=prompt,
            size="1792x1024",  # 16:9に最も近いDALL-E 3対応サイズ
            quality="standard",
            n=1,
        )
        img_url = response.data[0].url
        img_response = requests.get(img_url, timeout=60)
        if img_response.status_code != 200:
            raise RuntimeError(f"DALL-E 3 画像の取得に失敗しました (HTTP {img_response.status_code})")
        return Image.open(io.BytesIO(img_response.content))
