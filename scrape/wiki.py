""" Module for scraping prismata.gamepedia.com """
import requests

from bs4 import BeautifulSoup


def get_content(url):
    """
    Get HTML for URL.

    Parameters
    ----------
    url : str
        Valid URL to get content for.

    Returns
    -------
    str
        HTML content.

    """
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    return ""


def clean(value, cast=str):
    """
    Clean value provided.

    Parameters
    ----------
    value : bs4.element.Tag
        Tag object from BeautifulSoup4 library.
    cast : function, optional
        Funtion used to cast return into a type. Defaults to str.

    Returns
    -------
    any
        Returns content of Tag of the type from the cast function.

    """
    if value.div:
        value = value.div
    return cast(value.text.strip())


def unit_table_to_dict(data):
    """
    Parse HTML table from prismata.gamepedia.com into dict format.

    Parameters
    ----------
    data : str
        HTML table for unit list from prismata.gamepedia.com..

    Returns
    -------
    dict
        Unit information

    Example
    -------
    output:
        {
            "Unit Name":
                {
                    "url": "/Unit_Name",
                    "cost": {
                        "gold": 1,
                        "energy": 0,
                        "green": 1,
                        "blue": 0,
                        "red": 1,
                        },
                    "attack": 1,
                    "health": 1,
                    "supply": 1,
                    "frontline": True,
                    "fragile": False,
                    "blocker": True,
                    "prompt": False,
                    "stamina": 0,
                    "lifespan": 0,
                    "build_time": 0,
                    "exhaust_turn": 0,
                    "exhaust_ability": 0,
                    "type": 1,
                    "unit_spell": "Unit|Spell",
                },
            ...
        }

    """
    soup = BeautifulSoup(data, "html.parser")

    if not soup:
        return False, {"message": "Invalid format."}

    result = {}
    for row in soup.table("tr"):
        unit = row("td")
        if unit:
            result[clean(unit[0])] = {
                "url_path": unit[0].a.get("href"),
                "cost": {
                    "gold": clean(unit[3], int),
                    "energy": clean(unit[4], int),
                    "green": clean(unit[5], int),
                    "blue": clean(unit[6], int),
                    "red": clean(unit[7], int),
                    },
                "attack": int(clean(unit[15]) or 0),
                "health": clean(unit[10], int),
                "supply": clean(unit[8], int),
                "frontline": clean(unit[11], bool),
                "fragile": clean(unit[12], bool),
                "blocker": clean(unit[13], bool),
                "prompt": clean(unit[14], bool),
                "stamina": clean(unit[16], int),
                "lifespan": clean(unit[19], int),
                "build_time": clean(unit[9], int),
                "exhaust_turn": clean(unit[17], int),
                "exhaust_ability": clean(unit[18], int),
                "type": clean(unit[1], int),
                "unit_spell": clean(unit[2]),
                }
    return True, result
