from time import sleep
import board
from digitalio import DigitalInOut
from adafruit_character_lcd.character_lcd import Character_LCD_Mono


_CUSTOM_CHARS = {
    '°': [4, 10, 4, 0, 0, 0, 0, 0],
    '≈': [0, 8, 21, 2, 8, 21, 2, 0],
}

_CHAR_MAP = {char: chr(idx) for idx, char in enumerate(_CUSTOM_CHARS)}


def _translate_text(text: str) -> str:
    return ''.join(_CHAR_MAP.get(ch, ch) for ch in text)


lcd_columns = 16
lcd_rows = 2

lcd_rs = DigitalInOut(board.D26)
lcd_en = DigitalInOut(board.D19)
lcd_d4 = DigitalInOut(board.D13)
lcd_d5 = DigitalInOut(board.D6)
lcd_d6 = DigitalInOut(board.D5)
lcd_d7 = DigitalInOut(board.D12)

# Initialise the LCD class
lcd = Character_LCD_Mono(
    lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows
)

lcds = [
    Character_LCD_Mono(lcd_rs, DigitalInOut(board.D19), lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows),
    Character_LCD_Mono(lcd_rs, DigitalInOut(board.D16), lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)
]

for lcd in lcds:
    for idx, (symbol, bitmap) in enumerate(_CUSTOM_CHARS.items()):
        lcd.create_char(idx, bitmap)

for lcd in lcds:
    lcd.message = _translate_text('≈°↙↘↗↖↓↑←→')
