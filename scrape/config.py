""" Configuration for all things scrape. """
from random import uniform
from time import sleep


GENERAL = {
    # Wait between 1 and 3 seconds
    "THROTTLING_DELAY": lambda: sleep(uniform(1, 3)),
    }

PRISMATA_WIKI = {
    "BASE_URL": "https://prismata.gamepedia.com",
    "UNITS_PATH": "/Unit",
    }
