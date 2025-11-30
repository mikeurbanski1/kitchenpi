#!/bin/bash

_PID=$(ps aux | grep src.main | grep -v grep | tr -s ' ' | cut -d ' ' -f 2)

if [ -z "$_PID" ]; then
  echo "No process found"
else
  echo "Killing process $_PID"
  kill $_PID
fi