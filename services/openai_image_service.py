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

    def generate(self, prompt: str, reference_image=None) -> Image.Image:
        # ── Img2Img プレースホルダー ─────────────────────────────────
        # reference_image（ユーザーがアップロードした現在の部屋写真）が渡された場合、
        # 本来は gpt-image-1 の画像編集API（images.edit）に元画像を初期画像として渡し、
        # 「いまある部屋の構造・採光・窓位置を活かした」完成予想図を生成する想定。
        # 現状はコストと実装簡略化のため text→image 生成にフォールバックし、
        # 「既存レイアウトを尊重する」旨をプロンプトへ付与するに留める。
        # 本実装へ切り替える際は下行のコメントを外して _edit_from_reference() を呼ぶ。
        if reference_image is not None:
            prompt = self._with_reference_hint(prompt)
            # return self._edit_from_reference(prompt, reference_image)

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

    @staticmethod
    def _with_reference_hint(prompt: str) -> str:
        """参照画像がある場合に、既存の部屋構造を尊重させる指示を英語で付与する。"""
        return (
            prompt
            + " Keep the same room architecture, window positions, ceiling height, "
            "and overall proportions as the user's existing room; only restyle the "
            "furniture and decor."
        )

    def _edit_from_reference(self, prompt: str, reference_image: Image.Image) -> Image.Image:
        """【Img2Img 本実装の雛形 / 現在は未使用】

        アップロードされた現在の部屋写真を初期画像として gpt-image-1 の編集APIに渡し、
        既存空間を活かした完成予想図を生成する。実運用ではこのメソッドを generate() から
        呼び出すだけで text→image から Img2Img に切り替えられる。

        ※有効化前に要検証:
          - gpt-image-1 の images.edit が size="1536x1024"（横長）を許可するか
            （未対応なら正方形等にフォールバックが必要）
          - 入力画像の形式・サイズ・上限（PNG/正方形推奨か、要マスク有無）
          - 課金単価（編集APIは生成APIと従量単価が異なる場合がある）
        """
        buf = io.BytesIO()
        reference_image.save(buf, format="PNG")
        buf.seek(0)
        buf.name = "room.png"  # OpenAI SDK はファイル名から MIME を判定する
        response = self._client.images.edit(
            model=self._model,
            image=buf,
            prompt=prompt,
            size="1536x1024",
        )
        b64 = response.data[0].b64_json
        return Image.open(io.BytesIO(base64.b64decode(b64)))
