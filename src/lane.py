from __future__ import annotations

from enum import Enum


class Lane(Enum):
    """ Types of lane available """

    UNKNOWN = 0
    SLOW = 1
    MEDIUM = 2
    FAST = 3

    @staticmethod
    def get(key: str) -> Lane:
        try:
            return Lane[key]
        except KeyError:
            return Lane.UNKNOWN
