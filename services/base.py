from abc import ABC, abstractmethod
from PIL import Image


class CoordinateGeneratorBase(ABC):
    """インテリアコーディネート提案を生成するプロバイダーの共通インターフェース。"""

    @abstractmethod
    def generate(
        self,
        room_size: str,
        budget: int,
        taste: str,
        language: str = "Japanese",
        owned_items: str = "",
        base_color: str = "",
        accent_color: str = "",
    ) -> dict:
        """{"items": [...], "room_image_prompt": "..."} を返す。

        items の各要素は item_name / price / reason / placement / search_keyword を持つ。
        room_image_prompt は全アイテムを配置した部屋全体を描く英語の画像生成プロンプト。
        owned_items が指定された場合、その家具は提案・予算対象から除外する。
        base_color / accent_color が指定された場合、その配色を提案アイテムの色味と
        room_image_prompt に反映する（search_keyword には含めない）。空文字なら色は制約しない。
        """
        ...


class ImageGeneratorBase(ABC):
    """部屋の完成予想図を生成するプロバイダーの共通インターフェース。"""

    @abstractmethod
    def generate(self, prompt: str, reference_image=None) -> Image.Image:
        """PIL.Image を返す。失敗時は RuntimeError を raise する。

        reference_image（現在の部屋写真）が渡された場合は Img2Img の参照として扱う。
        """
        ...
