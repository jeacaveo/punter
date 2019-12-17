""" Configuration for all things scrape. """
from logging import (
    config as loggingConfig,
    getLogger,
    )
from os import path


GENERAL = {
    "THROTTLING_DELAY": (1, 3),  # Wait between 1 and 3 seconds
    }

PRISMATA_WIKI = {
    # Change BASE_URL to a URL to scrape from a site.
    "BASE_URL": "punter/scrape/files/wiki",  # "https://prismata.gamepedia.com"
    "UNITS_PATH": "/Unit",
    "SAVE_PATH": "punter/scrape/files/wiki",
    }

CURRENT_DIR = path.dirname(path.abspath(__file__))
loggingConfig.fileConfig(
    path.join(CURRENT_DIR, "../logging.conf"),
    defaults={"logfilename": path.join(CURRENT_DIR, "../../log")})
LOGGER = getLogger("scrape")
