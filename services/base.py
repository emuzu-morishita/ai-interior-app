from abc import ABC, abstractmethod
from PIL import Image


class CoordinateGeneratorBase(ABC):
    """インテリアコーディネート提案を生成するプロバイダーの共通インターフェース。"""

    @abstractmethod
    def generate(self, room_size: str, budget: int, taste: str, language: str = "Japanese") -> list[dict]:
        """提案アイテムのリストを返す。各要素は item_name / price / reason / image_prompt を持つ。"""
        ...


class ImageGeneratorBase(ABC):
    """部屋の完成予想図を生成するプロバイダーの共通インターフェース。"""

    @abstractmethod
    def generate(self, prompt: str) -> Image.Image:
        """PIL.Image を返す。失敗時は RuntimeError を raise する。"""
        ...
