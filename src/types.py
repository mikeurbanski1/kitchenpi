import datetime
from typing import TypedDict


class BaseWeather(TypedDict):
    condition: str
    wind_speed: int
    wind_gusts: int
    wind_dir: str


class PointInTimeWeather(BaseWeather):
    temp: int
    feels_like: int
    uv: int
    humidity: int
    cloud_cover: int


class CurrentWeather(PointInTimeWeather):
    pass


class DailyWeather(BaseWeather):
    date: datetime.date
    days_from_now: int
    temp: list[int]
    feels_like: list[int]
    precip: int
    avg_cloud_cover: int
    humidity: int


class HourlyWeather(PointInTimeWeather):
    time: datetime.datetime
    hours_from_now: int
    precip: int


class Weather(TypedDict):
    current_weather: CurrentWeather
    daily_forecast: list[DailyWeather]
    hourly_forecast: list[HourlyWeather]


class Pins(TypedDict):
    rs: int
    d4: int
    d5: int
    d6: int
    d7: int
    en: list[int]


class RotatingPart(TypedDict):
    lines_and_parts: list[list[str]]
    duration: int  # seconds
