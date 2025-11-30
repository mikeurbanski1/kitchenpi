#!/bin/bash

. config

API_KEY=$WEATHER_API_KEY LOG_LEVEL=$WEATHER_LOG_LEVEL LOG_FILE=log.log python -m src.main
