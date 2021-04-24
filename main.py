import argparse
import json
import re
from datetime import datetime, timedelta
from enum import Enum
from functools import cached_property

import pytz
import requests
from bs4 import BeautifulSoup

from config import API_URL, APP_ID, APP_KEY, PASSWORD, USERNAME


class Lane(Enum):
    """ Types of lane available """

    SLOW = 1
    MEDIUM = 2
    FAST = 3


class NoSlotsAvailable(Exception):
    """ For better semantics """

    pass


class Booker(object):
    def __init__(self, email: str, password: str):
        self.session = requests.Session()
        self.email = email
        self.password = password
        self.session.headers.update({"App-Id": APP_ID, "App-Key": APP_KEY})
        self.session.headers.update({"Auth-Token": self._sso_token})

    @cached_property
    def _api_url(self) -> str:
        return f"{API_URL}/37018"

    @cached_property
    def _auth_info(self) -> dict:
        token, company_id = self._login(self.email, self.password)
        url = f"{API_URL}/login/sso/{company_id}"
        res = self.session.post(url, data={"token": token})
        return json.loads(res.content)

    @cached_property
    def _company_id(self) -> int:
        return self._auth_info["_embedded"]["members"][0]["company_id"]

    @cached_property
    def _login_config(self) -> dict:
        res = self.session.get("https://www.nuffieldhealth.com/account/idaaslogin")
        soup = BeautifulSoup(res.text, "lxml")
        data_container = soup.find("script", {"data-container": True}).string
        return json.loads(re.search(r"var SETTINGS = (.*);", data_container).group(1))

    @cached_property
    def _member_id(self) -> int:
        return self._auth_info["_embedded"]["members"][0]["id"]

    @cached_property
    def _sso_token(self) -> str:
        return self._auth_info["auth_token"]

    @staticmethod
    def _transform(slot: dict) -> dict:
        start_time = datetime.strptime(slot["datetime"], "%Y-%m-%dT%H:%M:%S%z")
        lane = slot["description"].split(" ", 1)[0]
        return {
            "start_time": int(f"{start_time.hour:d}{start_time.minute:02d}"),
            "lane": Lane[lane.upper()],
            "event_id": slot["id"],
            "event_chain_id": slot["event_chain_id"],
        }

    def _checkout(self, slot: dict) -> None:
        data = {"entire_basket": True, "items": [slot]}
        self.session.post(f"{self._api_url}/basket/add_item", json=data)
        data = {"client": {"id": self._member_id}}
        self.session.post(f"{self._api_url}/basket/checkout", json=data)

    def _get_first_matching(self, slots: list, lane: Lane, start_time: int) -> dict:
        return next(
            {
                "event_id": slot["event_id"],
                "event_chain_id": slot["event_chain_id"],
                "member_id": self._member_id,
            }
            for slot in slots
            if slot["lane"] == lane and slot["start_time"] == start_time
        )

    def _get_slots_for(self, target_date: datetime) -> list:
        date_str = target_date.strftime("%Y-%m-%d")
        params = {
            "start_date": date_str,
            "end_date": date_str,
            "include_non_bookable": False,
        }
        res = self.session.get(f"{self._api_url}/events", params=params)
        return [
            Booker._transform(slot)
            for slot in json.loads(res.content)["_embedded"]["events"]
        ]

    def _login(self, email: str, password: str) -> tuple:
        self.session.headers.update({"X-CSRF-TOKEN": self._login_config["csrf"]})
        base_url = f"https://account.nuffieldhealth.com/{self._login_config['hosts']['tenant']}"
        params = {
            "tx": self._login_config["transId"],
            "p": self._login_config["hosts"]["policy"],
        }
        data = {"request_type": "RESPONSE", "email": email, "password": password}
        self.session.post(f"{base_url}/SelfAsserted", params=params, data=data)

        params.update({"csrf_token": self._login_config.get("csrf")})
        res = self.session.get(
            f"{base_url}/api/{self._login_config['api']}/confirmed", params=params
        )

        soup = BeautifulSoup(res.text, "lxml")
        url = soup.find("form", id="auto").get("action")
        code = soup.find("input", id="code").get("value")
        res = self.session.post(url, data={"code": code})

        soup = BeautifulSoup(res.text, "lxml")
        api_auth_info = soup.find("div", {"member-sso-login": True, "company-id": True})

        return api_auth_info.get("member-sso-login"), api_auth_info.get("company-id")

    def book(self, start: int, lane: Lane = Lane.MEDIUM, days_ahead: int = 8) -> None:
        """Books a swimming slot according to the specified filters.

        Parameters
        ----------
        start : int
            Desired slot start time, in HHMM format (e.g. 8AM -> 800 and 7PM -> 1900).
        lane : Lane, optional
            Desired lane to swim in, by default Lane.MEDIUM
        days_ahead : int, optional
            How many days forward to book for, by default 8

        Raises
        ------
        NoSlotsAvailable
            When the specified filters are too narrow.
        """
        today = datetime.now().astimezone(pytz.timezone("Europe/London"))
        target_date = today + timedelta(days=days_ahead)
        slots = self._get_slots_for(target_date)
        try:
            slot = self._get_first_matching(slots, lane, start)
            self._checkout(slot)
        except StopIteration as err:
            raise NoSlotsAvailable(
                f"No slots found for start_time={start}, lane={lane}, and target_date={target_date.date()}"
            ) from err


def main():
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
    args = parser.parse_args()
    booker = Booker(USERNAME, PASSWORD)
    booker.book(args.start_time, lane=Lane[args.lane], days_ahead=args.days_ahead)


if __name__ == "__main__":
    main()
