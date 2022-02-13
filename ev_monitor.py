#!/usr/bin/python3
""" Script to monitor networked device and send Telegram message
    if it changes online/offline status """

import configparser
import itertools
import json
import signal
import sys
import time
from collections import deque
from itertools import count

from ping3 import ping
from requests import request

config = configparser.ConfigParser()
config.read("ev_monitor.ini")

MONITOR_HOST = config["TARGET"]["Host"]
# MONITOR_DELAY = 1
MONITOR_DELAY = int(config["TARGET"]["MonitorDelaySecs"])
DEVICE_NAME = config["TARGET"]["DeviceName"]
FLIPFLOP_TOLERANCE = int(config["TARGET"]["FlipFlopTolerance"])
RETRIES = int(config["TARGET"]["PingRetries"])
RETRY_DELAY = int(config["TARGET"]["PingRetryDelay"])
TELEGRAM_API_TOKEN = config["TELEGRAM"]["ApiToken"]
TELEGRAM_CHANNEL_ID = config["TELEGRAM"]["ChannelId"]


def connect(host: str):
    """Generator of connection test result"""
    while True:
        yield bool(ping(host))


def connect_dummy(host: str):
    """Generator of connection fake test result"""
    yield from [True] * 4
    yield from [False] * (RETRIES + 1)
    yield from [True] * 5
    yield from [False] * (RETRIES + 1) * 10
    yield from itertools.repeat(True)


def retry(generator, max_attempts: int = 5):
    """Generic retry handler"""
    status = False  # Prevent lint errors regarding unbound variable
    for attempt, status in enumerate(generator, start=1):
        if status or attempt >= max_attempts:
            break
        print(f"Retrying in {RETRY_DELAY} seconds, attempt {attempt} = {status}")
        time.sleep(RETRY_DELAY)
    return status


class StableStatus:
    """Provide functions to smooth out status values to prevent flapping"""

    def __init__(self, status, window: int = (FLIPFLOP_TOLERANCE * 2) + 1):
        self._status_history = deque(maxlen=window)
        self._status_history.append(status)
        self._status = self._last_status = self.smoothed_status()

    def add(self, status: bool):
        """Add an entry to the status buffer"""
        self._status_history.append(status)
        self._last_status = self._status
        self._status = self.smoothed_status()

    def smoothed_status(self) -> bool:
        """Get the current smoothed status"""
        print(self._status_history)
        true_values = sum(self._status_history)
        false_values = len(self._status_history) - true_values
        return true_values >= false_values

    def status_changed(self) -> bool:
        """Return whether smoothed status has changed"""
        return self._last_status != self._status


def send_telegram(message_text):
    """Send a message via the Telegram Bot API"""
    telegram_base_url = f"https://api.telegram.org/bot{TELEGRAM_API_TOKEN}"
    channel_id = TELEGRAM_CHANNEL_ID

    params = {"chat_id": channel_id, "text": message_text}

    r = request("POST", f"{telegram_base_url}/sendMessage", params=params)
    if r.status_code != 200:
        print(r.status_code, flush=True)
        print(r.headers, flush=True)
        print(r.content, flush=True)
    # else:
    # response = json.loads(r.content)
    # print(json.dumps(response, indent=4, sort_keys=True))


def exit_handler(signalnum, frame):
    """Send shutdown message when our process is terminated"""
    send_telegram(
        f"☠ {DEVICE_NAME} monitor service terminating on signal '{signal.strsignal(signalnum)}' ☠"
    )
    sys.exit(0)


def friendly_status(status):
    """Return a human-readable text string based on status true/false"""
    return "✅ Online" if status else "❌ Offline"


def main():
    """Main Function"""

    check_connection = connect(MONITOR_HOST)
    status = StableStatus(next(check_connection))
    # status = StabilisedStatus(next(check_connection))

    send_telegram(
        f"{DEVICE_NAME} monitoring service has started.\nInitial status is {friendly_status(status.smoothed_status())}."
    )

    for iteration in count(start=1):
        print(
            f"Checking {DEVICE_NAME} (status counter is {iteration})...",
            flush=True,
        )
        status.add(retry(check_connection, RETRIES + 1))
        stable = status.smoothed_status()

        print(f"{iteration=} | {status.status_changed()=} | {stable=}", flush=True)

        if status.status_changed():
            send_telegram(f"Current {DEVICE_NAME} status is {friendly_status(stable)}")

        time.sleep(MONITOR_DELAY)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    main()
