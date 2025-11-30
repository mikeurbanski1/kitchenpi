def get_lcd_class(is_dev: bool):
    if is_dev:
        from src.lcd.lcd_mock import LCD as _LCD, PINS as _PINS
    else:
        from src.lcd.lcd import LCD as _LCD, PINS as _PINS  # type: ignore

    return _LCD, _PINS
