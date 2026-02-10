#!/bin/bash
# Convenient wrapper for Trade Republic Tracker

if [ -z "$TR_PHONE" ] || [ -z "$TR_PIN" ]; then
  echo "Error: Please set TR_PHONE (international format) and TR_PIN in your environment."
  echo "Example: export TR_PHONE=\"+4915112345678\" export TR_PIN=\"1234\""
  exit 1
fi

PYTHONPATH=src python3 -m src.tracker.cli "$@"
