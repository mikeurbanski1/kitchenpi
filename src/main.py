import argparse
import logging
import sys
import time
import traceback

from src.lcd.lcd_manager import LcdManager

from src.types import CurrentWeather, DailyWeather, HourlyWeather, Weather
import src.utils as utils
from src.weather import open_meteo


logger = logging.getLogger(__name__)

LOCATIONS = {
    'Minneapolis': {'lat': 44.9778, 'lon': -93.2650},
    'Seattle': {'lat': 47.6062, 'lon': -122.3321},
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dev',
        action='store_true',
        help='Run in development mode (no LCD, just print to console, no log file)',
    )
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'error', 'off'],
        default='info',
        help='Set the logging level (debug, info, error, off). Default is info.',
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default='kitchenpi.log',
        help='Set the log file path (appends to file if it exists, unless in dev mode, which clears the file on startup)',
    )
    parser.add_argument(
        '--refresh-interval',
        type=int,
        default=2,
        help='Set the refresh interval in minutes. Cannot be less than 1. Default is 2 minutes.',
    )
    parser.add_argument(
        '--location',
        type=str,
        choices=LOCATIONS.keys(),
        default='Minneapolis',
        help=f'Set the location for weather data ({", ".join(LOCATIONS.keys())})',
    )
    parser.add_argument(
        '--lcd-test',
        action='store_true',
        help='Run a test pattern on the LCDs and exit',
    )
    return parser.parse_args()


def run_test_pattern(args):
    print('Running LCD test pattern...')
    lcd_manager = LcdManager(is_dev=args.dev)
    parts = [
        ['A', 'Test', 'Line 1'],
        [
            'Chars:',
            f'{utils.DEGREES}{utils.WIND}{utils.CLOUD}',
            f'{utils.HUMIDITY}{utils.PRECIP}{utils.SUN}',
        ],
    ]

    for lcd_index in range(len(lcd_manager.lcds)):
        lcd_manager.set_text_parts(lcd_index, parts, print_dev=True)
        time.sleep(2)
    sys.exit(0)


def init_logging(args):
    if args.log_file and not args.dev:
        handler = logging.FileHandler(args.log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)

    logging.basicConfig(
        level=utils.get_log_level(args.log_level),
        format='[%(asctime)s][%(levelname)s] %(message)s',
        handlers=[handler],
    )


def get_weather(
    location: dict[str, float],
) -> Weather:
    return open_meteo.get_weather(location['lat'], location['lon'])


def handle_today_display(
    lcd_index: int,
    lcd_manager: LcdManager,
    current_weather: CurrentWeather,
    today_weather: DailyWeather,
):
    current_weather_parts = [
        [
            f'={current_weather["temp"]}{utils.DEGREES}',
            f'{utils.APPROX}{current_weather["feels_like"]}{utils.DEGREES}',
            f'{current_weather["condition"]}',
        ],
        [
            f'{utils.WIND}{current_weather["wind_speed"]}/{current_weather["wind_gusts"]}{current_weather["wind_dir"]}',
            f'{utils.HUMIDITY}{current_weather["humidity"]}%',
        ],
    ]

    today_weather_parts = [
        [
            f'={today_weather["temp"][0]}/{today_weather["temp"][1]}{utils.DEGREES}',
            f'{utils.APPROX}{today_weather["feels_like"][0]}/{today_weather["feels_like"][1]}{utils.DEGREES}',
        ],
        [
            f'{utils.PRECIP}{today_weather["precip"]}%',
            f'{utils.CLOUD}{today_weather["avg_cloud_cover"]}%',
            f'{utils.SUN}{current_weather["uv"]}',
        ],
    ]

    lcd_manager.set_rotating_text_parts(
        lcd_index,
        [
            {
                'lines_and_parts': current_weather_parts,
                'duration': 5,
            },
            {
                'lines_and_parts': today_weather_parts,
                'duration': 5,
            },
        ],
    )


def handle_forecast_display(
    lcd_index: int, lcd_manager: LcdManager, forecast: list[DailyWeather]
):
    lcd_manager.set_rotating_text_parts(
        1,
        [
            {
                'lines_and_parts': utils.get_daily_weather_output_parts(day),
                'duration': 5,
            }
            for day in forecast[1:4]
        ],
    )


def handle_hourly_display(
    lcd_index: int, lcd_manager: LcdManager, hourly_forecast: list[HourlyWeather]
):
    lcd_manager.set_rotating_text_parts(
        lcd_index,
        [
            {
                'lines_and_parts': [
                    [
                        f'{hour["time"].strftime("%H")}:',
                        f'{hour["temp"]}{utils.DEGREES}',
                        f'{hour["condition"]}',
                    ],
                    [
                        f'{utils.WIND}{hour["wind_speed"]}/{hour["wind_gusts"]}{hour["wind_dir"]}',
                        f'{utils.PRECIP}{hour["precip"]}%',
                    ],
                ],
                'duration': 3,
            }
            for hour in hourly_forecast[2:10:2]  # Every 2 hours, up to 8 hours from now
        ],
    )


def run(args):
    if args.refresh_interval < 1:
        logger.warning(
            'Refresh interval cannot be less than 1 minute. Setting to 1 minute.'
        )
        args.refresh_interval = 1

    lcd_manager = LcdManager(is_dev=args.dev)

    while True:
        try:
            weather = get_weather(LOCATIONS[args.location])

            handle_today_display(
                0, lcd_manager, weather['current_weather'], weather['daily_forecast'][0]
            )
            handle_forecast_display(1, lcd_manager, weather['daily_forecast'])
            handle_hourly_display(2, lcd_manager, weather['hourly_forecast'])

            # lcd_manager.print_all()
        except Exception as e:
            logger.error(f'Error getting weather data: {e}')
            logger.debug(traceback.format_exc())

        time.sleep(args.refresh_interval * 60)


def main():
    args = parse_args()

    if args.lcd_test:
        run_test_pattern(args)
    else:
        init_logging(args)
        run(args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
