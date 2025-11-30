import os
import requests

from src.types import CurrentWeather

api_key = os.getenv('API_KEY')
api_key_param = {'key': api_key}

base_url = 'http://api.weatherapi.com/v1'


payload = {}
headers = {}


def get_weather(q='55418') -> CurrentWeather:
    url = f'{base_url}/current.json'
    response = requests.get(url, params={'q': q, **api_key_param})
    current = response.json()['current']

    return {
        'temp': round(current['temp_f']),
        'condition': current['condition']['text'],
        'wind': round(current['wind_mph']),
        'wind_dir': current['wind_dir'],
        'humidity': current['humidity'],
        'cloud': current['cloud'],
        'feels_like': round(current['feelslike_f']),
        'heat_index': round(current['heatindex_f']),
        'uv': current['uv']
    }
