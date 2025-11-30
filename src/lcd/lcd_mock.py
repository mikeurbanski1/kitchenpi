from src.types import Pins

PINS: Pins = {
    'rs': 26,
    'd4': 13,
    'd5': 6,
    'd6': 5,
    'd7': 12,
    'en': [15],
}


class LCD:
    def __init__(self, en: int, width=16, height=2, rs=1, d4=2, d5=3, d6=4, d7=5):
        self.text = ''
        self.width = width
        self.height = height

    def set_text(self, text: str):
        self.text = text

    def clear(self):
        self.text = ''
