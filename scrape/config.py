""" Configuration for all things scrape. """


GENERAL = {
    "THROTTLING_DELAY": (1, 3),  # Wait between 1 and 3 seconds
    }

PRISMATA_WIKI = {
    "BASE_URL": "https://prismata.gamepedia.com",
    "UNITS_PATH": "/Unit",
    "SAVE_PATH": "scrape/files/wiki",
    }
