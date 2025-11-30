import json
import logging
import os
from typing import TypedDict
from collections import Counter
import requests  # type: ignore

from src.types import CurrentWeather, DailyWeather, HourlyWeather, Weather
from src.utils import (
    prob_any_persistence,
    wind_degree_to_dir,
)
from datetime import datetime


logger = logging.getLogger(__name__)

api_key = os.getenv('API_KEY')
api_key_param = {'key': api_key}


base_url = 'https://api.open-meteo.com/v1/forecast'


class _CurrentWeatherResponse(TypedDict):
    time: str
    interval: int
    wind_speed_10m: float
    wind_direction_10m: int
    wind_gusts_10m: float
    temperature_2m: float
    relative_humidity_2m: int
    apparent_temperature: float
    is_day: int
    precipitation: float
    rain: float
    showers: float
    snowfall: float
    weather_code: int
    cloud_cover: int
    pressure_msl: float
    surface_pressure: float


class _DailyWeatherResponse(TypedDict):
    time: list[str]
    weather_code: list[int]
    temperature_2m_max: list[float]
    temperature_2m_min: list[float]
    apparent_temperature_max: list[float]
    apparent_temperature_min: list[float]
    precipitation_hours: list[float]
    precipitation_probability_max: list[int]
    wind_speed_10m_max: list[float]
    wind_gusts_10m_max: list[float]
    wind_direction_10m_dominant: list[int]
    uv_index_max: list[float]
    cloud_cover_mean: list[int]
    relative_humidity_2m_mean: list[int]


class _HourlyWeatherResponse(TypedDict):
    time: list[str]
    temperature_2m: list[float]
    apparent_temperature: list[float]
    precipitation_probability: list[int]
    weather_code: list[int]
    cloud_cover: list[int]
    wind_speed_10m: list[float]
    wind_direction_10m: list[int]
    wind_gusts_10m: list[float]
    uv_index: list[float]


class _WeatherResponse(TypedDict):
    current: _CurrentWeatherResponse
    daily: _DailyWeatherResponse
    hourly: _HourlyWeatherResponse


def _get_current_weather(weather: _WeatherResponse) -> CurrentWeather:
    current = weather['current']
    hourly = weather['hourly']
    return {
        'temp': round(current['temperature_2m']),
        'condition': weather_code_to_condition(current['weather_code']),
        'wind_speed': round(current['wind_speed_10m']),
        'wind_gusts': round(current['wind_gusts_10m']),
        'wind_dir': wind_degree_to_dir(current['wind_direction_10m']),
        'humidity': current['relative_humidity_2m'],
        'cloud_cover': current['cloud_cover'],
        'feels_like': round(current['apparent_temperature']),
        'uv': round(hourly['uv_index'][0]),
    }


def _get_daily_weather(weather: _WeatherResponse, day_index: int) -> DailyWeather:
    daily = weather['daily']
    hourly = weather['hourly']
    today_date = daily['time'][day_index]  # Today's date in the format 'YYYY-MM-DD'
    today_timestamps = len(
        [timestamp for timestamp in hourly['time'] if timestamp.startswith(today_date)]
    )
    precip = prob_any_persistence(
        hourly['precipitation_probability'][:today_timestamps]
    )
    return {
        'date': datetime.strptime(daily['time'][day_index], '%Y-%m-%d').date(),
        'days_from_now': 0,
        'condition': weather_code_to_condition(daily['weather_code'][0]),
        'temp': [
            round(daily['temperature_2m_max'][day_index]),
            round(daily['temperature_2m_min'][day_index]),
        ],
        'feels_like': [
            round(daily['apparent_temperature_max'][day_index]),
            round(daily['apparent_temperature_min'][day_index]),
        ],
        'precip': precip,
        'wind_speed': round(daily['wind_speed_10m_max'][day_index]),
        'wind_gusts': round(daily['wind_gusts_10m_max'][day_index]),
        'wind_dir': wind_degree_to_dir(daily['wind_direction_10m_dominant'][day_index]),
        'avg_cloud_cover': daily['cloud_cover_mean'][day_index],
        'humidity': daily['relative_humidity_2m_mean'][day_index],
    }


def _get_forecast(weather: _WeatherResponse) -> list[DailyWeather]:
    daily = weather['daily']
    num_days = len(daily['time'])
    return [_get_daily_weather(weather, i) for i in range(num_days)]


def _get_hourly_forecast(weather: _WeatherResponse) -> list[HourlyWeather]:
    hourly = weather['hourly']
    num_hours = len(hourly['time'])
    forecast: list[HourlyWeather] = []
    for i in range(num_hours):
        forecast.append(
            {
                'time': datetime.strptime(hourly['time'][i], '%Y-%m-%dT%H:%M'),
                'hours_from_now': i,
                'temp': round(hourly['temperature_2m'][i]),
                'feels_like': round(hourly['apparent_temperature'][i]),
                'precip': hourly['precipitation_probability'][i],
                'condition': weather_code_to_condition(hourly['weather_code'][i]),
                'wind_speed': round(hourly['wind_speed_10m'][i]),
                'wind_gusts': round(hourly['wind_gusts_10m'][i]),
                'wind_dir': wind_degree_to_dir(hourly['wind_direction_10m'][i]),
                'humidity': hourly['cloud_cover'][i],
                'cloud_cover': hourly['cloud_cover'][i],
                'uv': round(hourly['uv_index'][i]),
            }
        )
    return forecast


last_50_response_codes: list[int] = []
num_requests: int = 0


def get_weather(lat: float, lon: float) -> Weather:
    url = base_url
    params = {
        'latitude': lat,
        'longitude': lon,
        'daily': 'uv_index_max,weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_hours,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant,cloud_cover_mean,relative_humidity_2m_mean',
        'hourly': 'uv_index,temperature_2m,apparent_temperature,precipitation_probability,weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m',
        'current': 'wind_speed_10m,wind_direction_10m,wind_gusts_10m,temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,surface_pressure',
        'timezone': 'America/Chicago',
        'wind_speed_unit': 'mph',
        'temperature_unit': 'fahrenheit',
        'precipitation_unit': 'inch',
        'forecast_hours': '24',
    }

    logger.debug(f'Fetching weather from Open-Meteo: {url} with params {params}')

    response = requests.get(
        url,
        params=params,
    )

    global num_requests
    num_requests += 1

    last_50_response_codes.append(response.status_code)
    if len(last_50_response_codes) > 50:
        last_50_response_codes.pop(0)

    if num_requests % 25 == 0:
        logger.info(
            f'Last 50 responses by status: {dict(Counter(last_50_response_codes))}'
        )

    if response.status_code != 200:
        logger.error(
            f'Got bad response from Open-Meteo: {response.status_code} {response.text}'
        )
        raise Exception(f'Got bad response from Open-Meteo: {response.status_code}')

    weather: _WeatherResponse = response.json()
    logger.debug(
        f'Got weather response (code: {response.status_code}): {json.dumps(weather)}'
    )

    return {
        'current_weather': _get_current_weather(weather),
        'daily_forecast': _get_forecast(weather),
        'hourly_forecast': _get_hourly_forecast(weather),
    }


_WEATHER_CODES = {
    0: 'Clear',
    1: 'Clear',
    2: 'Pt.Cl.',
    3: 'Cloudy',
    45: 'Fog',
    48: 'Fog',
    51: '~Driz',
    53: 'Driz',
    55: 'Driz!',
    56: 'FrzDrz',
    57: 'FrzDrz!',
    61: '~Rain',
    63: 'Rain',
    65: 'Rain!',
    66: 'FrzRain',
    67: 'FrzRain!',
    71: '~Snow',
    73: 'Snow',
    75: 'Snow!',
    77: 'Snow',
    80: '~Shower',
    81: 'Shower',
    82: 'Shower!',
    85: 'SnShowr',
    86: 'SnShowr!',
    95: 'Storm',
    96: 'Storm',
    99: 'Storm',
}


def weather_code_to_condition(code: int) -> str:
    if code not in _WEATHER_CODES:
        logger.error(f'Got unknown weather code: {code}')
    return _WEATHER_CODES.get(code, f'{code}(?)')
