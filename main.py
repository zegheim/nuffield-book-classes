from __future__ import annotations

import argparse
import logging
from datetime import datetime

import pytz
from dotenv import dotenv_values

from config import BOOKING_OPEN_TIME
from src.booker import Booker
from src.lane import Lane
from src.log import get_logger


def main():
    logger = get_logger("main", level=logging.DEBUG)
    today = datetime.now().astimezone(pytz.timezone("Europe/London"))
    logger.info(f"Local time now is {today}.")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "start_time",
        metavar="START_TIME",
        type=int,
        help="Desired slot start time, in HHMM format (e.g. 8AM -> 800 and 7PM -> 1900).",
    )
    parser.add_argument(
        "-l",
        "--lane",
        metavar="LANE",
        type=str,
        choices=[l.name for l in Lane],
        default="MEDIUM",
        help="Desired lane to swim in. One of SLOW, MEDIUM, or FAST. Default = MEDIUM.",
    )
    parser.add_argument(
        "-d",
        "--days-ahead",
        metavar="N",
        type=int,
        default=8,
        help="How many days forward to book for, by default 8.",
    )
    parser.add_argument(
        "-e",
        "--env",
        metavar="PATH_TO_ENV_FILE",
        type=str,
        default=".env",
        help="Path to .env file containing authentication information. Defaults to .env",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, bypasses the hour check. Useful for debugging purposes.",
    )

    args = parser.parse_args()
    logger.debug(f"Parsed args={args}")

    if today.hour != BOOKING_OPEN_TIME and not args.dry_run:
        logger.warning(f"{today.hour} != {BOOKING_OPEN_TIME}. Skipping...")
        return

    env = dotenv_values(args.env)
    booker = Booker(env["EMAIL"], env["PASSWORD"])
    booker.book(args.start_time, lane=Lane[args.lane], days_ahead=args.days_ahead)


if __name__ == "__main__":
    main()
