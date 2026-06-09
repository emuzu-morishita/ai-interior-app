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
    ) -> list[dict]:
        """提案アイテムのリストを返す。各要素は item_name / price / reason / image_prompt を持つ。

        owned_items が指定された場合、その家具は提案・予算対象から除外する。
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
