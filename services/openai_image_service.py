import base64
import io
from PIL import Image
from openai import OpenAI

from services.base import ImageGeneratorBase


class OpenAIImageGenerator(ImageGeneratorBase):
    def __init__(self, api_key: str, model: str = "gpt-image-1", quality: str = "medium"):
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._quality = quality

    def generate(self, prompt: str) -> Image.Image:
        response = self._client.images.generate(
            model=self._model,
            prompt=prompt,
            size="1536x1024",  # 横長（部屋全体が映る画角）
            quality=self._quality,
            n=1,
        )
        # gpt-image-1 は常に base64 で返す（URLではない）
        b64 = response.data[0].b64_json
        return Image.open(io.BytesIO(base64.b64decode(b64)))
