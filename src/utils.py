from __future__ import annotations

import logging
import threading
import time

from src.types import DailyWeather, RotatingPart

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.lcd.lcd_manager import LcdManager


# MISC UTILS


def get_log_level(level: str) -> int:
    level = level.lower()
    if level == 'debug':
        return logging.DEBUG
    elif level == 'info':
        return logging.INFO
    elif level == 'error':
        return logging.ERROR
    elif level == 'off':
        return logging.CRITICAL + 1
    else:
        raise Exception(f'Invalid log level: {level}')


lcd_manager_lock = threading.Lock()
thread_update_lock = threading.Lock()


class RotatingDisplayThread(threading.Thread):
    def __init__(
        self, rotation: list[RotatingPart], lcd_manager: LcdManager, lcd_index: int
    ) -> None:
        super().__init__(daemon=True)
        self.rotation = rotation
        self.lcd_manager = lcd_manager
        self.lcd_index = lcd_index
        self.current_index = 0
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            with lcd_manager_lock:
                current_part = self.rotation[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.rotation)
                self.lcd_manager.set_text_parts(
                    self.lcd_index, current_part['lines_and_parts']
                )
            time.sleep(current_part['duration'])

    def stop(self):
        self._stop_event.set()

    def set_rotation(self, rotation: list[RotatingPart]):
        with thread_update_lock:
            self.rotation = rotation
            if self.current_index >= len(self.rotation):
                self.current_index = 0


# WEATHER UTILS


_WIND_DIRS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']


def wind_degree_to_dir(deg: int) -> str:
    if deg == 360:
        deg = 0

    for idx, dir in enumerate(
        range(0, 361, 45)
    ):  # do 360 as well, to catch values west of north
        if dir - 22.5 < deg < dir + 22.5:
            return _WIND_DIRS[idx % len(_WIND_DIRS)]

    raise Exception(f'Failed to get wind direction label for direction {deg}')


def prob_any_persistence(hourly_pop: list[int], D=2.0) -> int:
    """
    D = average duration (hours) of a rain event.
    s_i = min(p_i / D, 1.0) approximates chance an event starts in hour i.
    """
    prob_no_start = 1.0
    for p in hourly_pop:
        s = min((p / 100.0) / D, 1.0)
        prob_no_start *= 1.0 - s

    return round((1.0 - prob_no_start) * 100.0)


# STRING UTILS


def justify_text_parts(parts: list[str], width: int) -> str:
    joined = ''.join(parts)
    if len(joined) >= width or len(parts) <= 1:
        return joined
    # TODO only supports up to 3 parts, but it seems like plenty for a 16 char width
    # I am sure there is a cool and general way to do this
    elif len(parts) == 2:
        return parts[0].ljust(width - len(parts[1])) + parts[1]
    elif len(parts) == 3:
        return (
            parts[0] + parts[1].center(width - len(parts[0]) - len(parts[2])) + parts[2]
        )

    return joined


# OUTPUT


DEGREES = '°'
APPROX = '≈'
WIND = '≋'
CLOUD = '☁'
HUMIDITY = '⸪'
PRECIP = '🌧'
SUN = '☼'


def get_daily_weather_output_parts(daily_weather: DailyWeather) -> list[list[str]]:
    return [
        [
            daily_weather['date'].strftime('%a'),
            f'{daily_weather["temp"][0]}{DEGREES}/{daily_weather["temp"][1]}{DEGREES}',
        ],
        [
            f'{daily_weather["condition"]}',
            f'{HUMIDITY}{daily_weather["humidity"]}%',
            f'{PRECIP}{daily_weather["precip"]}%',
        ],
    ]


def get_lcd_lines(text: str, width=16, height=2) -> list[str]:
    text_lines = text.split('\n')

    header = '┌' + ('─' * width) + '┐'
    footer = '└' + ('─' * width) + '┘'
    return_lines = [header]

    for row in range(0, height):
        return_lines.append(
            f'│{text_lines[row].ljust(width) if len(text_lines) > row else "".ljust(width)}│'
        )

    return_lines.append(footer)

    return return_lines


def print_lcds(lcds):
    # array of arrays: each outer array is an LCD, and each inner array is the array of lines for that LCD
    lcd_lines = list(
        map(
            lambda lcd: get_lcd_lines(lcd.text, width=lcd.width, height=lcd.height),
            lcds,
        )
    )

    max_rows = max(map(lambda _lines: len(_lines), lcd_lines))

    for row in range(0, max_rows):
        for index, lines in enumerate(lcd_lines):
            # TODO handle LCDs of different sizes?
            if len(lines) > row:
                print(lines[row], end='  ')
        print()
