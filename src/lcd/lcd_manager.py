import threading
from typing import TypedDict
from src.lcd import get_lcd_class
from src.types import RotatingPart
from src.utils import RotatingDisplayThread, justify_text_parts, print_lcds


class DisplayThread(TypedDict):
    thread: threading.Thread
    lcd: int


class LcdManager:
    def __init__(self, is_dev: bool) -> None:
        self.is_dev = is_dev
        LCD, PINS = get_lcd_class(is_dev)
        self.lcds = [
            LCD(
                en=en_pin,
                width=16,
                height=2,
                rs=PINS['rs'],
                d4=PINS['d4'],
                d5=PINS['d5'],
                d6=PINS['d6'],
                d7=PINS['d7'],
            )
            for en_pin in PINS['en']
        ]

        self.rotating_display_threads: dict[int, RotatingDisplayThread] = {}

        self.threads: list[DisplayThread] = []

    def clear_all(self) -> None:
        for idx, _ in enumerate(self.lcds):
            self.clear(idx)
        self._print()

    def clear(self, lcd_index: int) -> None:
        self.lcds[lcd_index].clear()
        self._print()

    def set_text(self, lcd_index: int, text: str, print_dev: bool = True) -> None:
        self.clear(lcd_index)
        self.lcds[lcd_index].set_text(text)
        if print_dev:
            self._print()

    # array is array of lines, each is an array of parts.
    # set 1, 2, or 3 parts per line, array is array of lines
    # parts will be justified as best as possible
    # ex: with width = 16, set_text_parts([['abc', 'xyz']]) adds middle padding and results in 'abc          xyz'
    # set_text_parts([['abc', 'qwe', 'xyz']]) centers the second part and right-justifies the third: 'abc   qwe    xyz'
    def set_text_parts(
        self, lcd_index: int, lines_and_parts: list[list[str]], print_dev: bool = True
    ) -> None:
        text = '\n'.join(
            map(
                lambda parts: justify_text_parts(parts, self.lcds[lcd_index].width),
                lines_and_parts,
            )
        )
        self.set_text(lcd_index, text, print_dev=print_dev)

    def set_rotating_text_parts(
        self, lcd_index: int, rotation: list[RotatingPart]
    ) -> None:
        if lcd_index in self.rotating_display_threads:
            self.rotating_display_threads[lcd_index].set_rotation(rotation)
        else:
            thread = RotatingDisplayThread(
                rotation=rotation, lcd_manager=self, lcd_index=lcd_index
            )
            self.rotating_display_threads[lcd_index] = thread
            thread.start()

    def _print(self) -> None:
        if self.is_dev:
            print_lcds(self.lcds)

    def print_all(self) -> None:
        print_lcds(self.lcds)
