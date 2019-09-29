""" Utility functions for scrape module. """
from random import uniform
from time import sleep

from typing import Tuple

from punter.scrape.config import GENERAL


def delay(secs: Tuple[int, int] = GENERAL["THROTTLING_DELAY"]) -> float:
    """
    Wait for a random amount of time between two numbers (in seconds).

    Parameters
    ----------
    secs : tuple
        Range of seconds to wait for.

    Returns
    -------
    float
        Amount of time waited.

    """
    value: float = uniform(secs[0], secs[1])
    sleep(value)
    return value
