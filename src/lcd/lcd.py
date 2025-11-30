import board  # type: ignore
from digitalio import DigitalInOut  # type: ignore
from adafruit_character_lcd.character_lcd import Character_LCD_Mono  # type: ignore

import logging

from src.types import Pins

logger = logging.getLogger(__name__)


PINS: Pins = {
    'rs': board.D5,  # LCD pin 4
    'd4': board.D6,  # LCD pin 11
    'd5': board.D13,  # LCD pin 12
    'd6': board.D19,  # LCD pin 13
    'd7': board.D26,  # LCD pin 14
    'en': [board.D16, board.D20, board.D21],  # LCD pin 6
}

# https://www.quinapalus.com/hd44780udg.html
_CUSTOM_CHARS = {
    '°': [4, 10, 4, 0, 0, 0, 0, 0],
    '≈': [0, 8, 21, 2, 8, 21, 2, 0],
    '≋': [8, 21, 2, 8, 21, 2, 24, 7],
    '⸪': [18, 18, 9, 9, 18, 18, 9, 9],
    '☁': [10, 21, 31, 0, 0, 0, 0, 0],
    '🌧': [10, 21, 31, 0, 4, 21, 21, 17],
    '☼': [4, 21, 14, 27, 14, 21, 4, 0],
    '~': [0, 0, 8, 21, 2, 0, 0, 0],
}


_CHAR_MAP = {char: chr(idx) for idx, char in enumerate(_CUSTOM_CHARS)}


def _translate_text(text: str) -> str:
    for idx, (key, _) in enumerate(_CHAR_MAP.items()):
        text = text.replace(key, chr(idx))
    return text


class LCD:
    def __init__(self, en, width, height, rs, d4, d5, d6, d7):
        self.lcd = Character_LCD_Mono(
            DigitalInOut(rs),
            DigitalInOut(en),
            DigitalInOut(d4),
            DigitalInOut(d5),
            DigitalInOut(d6),
            DigitalInOut(d7),
            width,
            height,
        )
        self._init_custom_chars()
        self.text = ''
        self.width = width
        self.height = height

    def _init_custom_chars(self):
        for idx, (symbol, bitmap) in enumerate(_CUSTOM_CHARS.items()):
            logger.debug(f'Adding custom char: {idx} {symbol} {bitmap}')
            self.lcd.create_char(idx, bitmap)

    def set_text(self, text: str):
        self.lcd.message = _translate_text(text)
        self.text = text

    def clear(self):
        self.lcd.clear()
        self.text = ''
