""" Configuration for all things scrape. """


GENERAL = {
    "THROTTLING_DELAY": (1, 3),  # Wait between 1 and 3 seconds
    }

PRISMATA_WIKI = {
    # Change BASE_URL to a path to a directory to avoid making http requests
    "BASE_URL": "https://prismata.gamepedia.com",
    "UNITS_PATH": "/Unit",
    "SAVE_PATH": "scrape/files/wiki",
    }
