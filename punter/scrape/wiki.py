""" Module for scraping prismata.gamepedia.com """
import csv
import json
import os
import re
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Union,
    )

import requests
from bs4 import (
    BeautifulSoup,
    element as bs4_element,
    )

from punter.scrape.config import (
    LOGGER as logger,
    PRISMATA_WIKI,
    )
from punter.scrape.utils import delay


# Map symbol titles into str abbreviation
TITLE_SYMBOL_MAP: Dict[str, str] = {
    "Gold": "",
    "Energy": "E",
    "Green resource": "G",
    "Blue resource": "B",
    "Red resource": "R",
    "Attack": "X",
    "Ability": "Click",
    }


def get_content(path: str, save_file: bool = False) -> str:
    """
    Get HTML for path.

    Parameters
    ----------
    path : str
        Valid path to get content from.
    save_file : bool, defaults to False
        Saves a file to configed save path if not reading from a file.

    Returns
    -------
    str
        HTML content.

    """
    read_file = not path.startswith("http")
    if read_file and os.path.isfile(path):
        with open(path, "r") as local_file:
            content = local_file.read()
            is_valid = True
    else:
        response = requests.get(path)
        content = str(response.content)
        is_valid = response.status_code == 200

    if not is_valid:
        return ""

    if save_file and not read_file:
        with open(path, "w") as out_file:
            out_file.write(BeautifulSoup(content, "html.parser").prettify())
    return content


def clean(element: bs4_element, cast: Callable[[Any], Any] = str) -> Any:
    """
    Clean item provided.

    Parameters
    ----------
    item : bs4.element.Tag
        Tag object from BeautifulSoup4 library.
    cast : function, optional
        Funtion used to cast return into a type. Defaults to str.

    Returns
    -------
    any
        Returns content of Tag of the type from the cast function.

    """
    if element.div:
        element = element.div
    # element.img is for fields that only contain an image and no text
    value = element.img or element.text.strip()
    return cast(value)


def unit_table_to_dict(
        data: str) -> Dict[str, Dict[str, Union[Dict[str, int], str, int]]]:
    """
    Parse HTML unit table from prismata.gamepedia.com into dict format.

    Parameters
    ----------
    data : str
        HTML table for unit list from prismata.gamepedia.com..

    Returns
    -------
    dict

    Example
    -------
    output:
        {
            "Unit Name":
                {
                    "name": "Unit Name",
                    "costs": {
                        "gold": 1,
                        "energy": 0,
                        "green": 1,
                        "blue": 0,
                        "red": 1,
                        },
                    "stats": {
                        "attack": 1,
                        "health": 1,
                        },
                    "attributes": {
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
                        },
                    "links": {
                        "path": "/Unit_Name",
                        },
                    "type": 1,
                    "unit_spell": "Unit|Spell",
                },
            ...
        }

    """
    soup = BeautifulSoup(data, "html.parser")
    table = soup.table("tr") if soup.table else []

    return {
        clean(unit[0]): {  # unit name
            "name": clean(unit[0]),
            "costs": {
                "gold": clean(unit[3], int),
                "energy": clean(unit[4], int),
                "green": clean(unit[5], int),
                "blue": clean(unit[6], int),
                "red": clean(unit[7], int),
                },
            "stats": {
                "attack": int(clean(unit[15]) or 0),
                "health": clean(unit[10], int),
                },
            "attributes": {
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
                },
            "links": {
                "path": unit[0].a.get("href"),
                },
            "type": clean(unit[1], int),
            "unit_spell": clean(unit[2]),
            }
        for unit in map(lambda row: row("td"), table)  # type: ignore
        if unit
        # Ignoring typing in map, all uses of the clean function return Any
        # This means that it can't match the return types for this function
        }


def clean_symbols(element: bs4_element.Tag) -> bs4_element.Tag:
    """
    Change symbol links into text..

    Parameters
    ----------
    element : bs4.element.Tag
        Tag object from BeautifulSoup4 library.

    Returns
    -------
    bs4.element.Tag
        Returns the same element provided as parameter,
        but with all symbol links replaced.

    """
    for icon in element("a"):
        title = icon.get("title") or icon.text
        symbol = TITLE_SYMBOL_MAP.get(title, title)
        icon.replace_with(symbol)
    return element


def clean_changes(element: bs4_element.Tag) -> List[str]:
    """
    Clean changes list into readable format.

    Parameters
    ----------
    item : bs4.element.Tag
        Tag object from BeautifulSoup4 library.

    Returns
    -------
    list(str)
        Returns list of changes in string representation.

    """
    clean_values = []
    for item in element.ul("li"):
        item = clean_symbols(item)
        content = item.get_text().replace("\n", "")
        clean_values.append(" ".join(content.split()))
    return clean_values


def clean_change_log(change_log: bs4_element.Tag) -> Dict[str, List[str]]:
    """
    Clean change log element into readable format.

    Parameters
    ----------
    change_log: bs4.element.Tag
        Tag object from BeautifulSoup4 library.

    Returns
    -------
    dict
        Returns list of changes cleaner format.

    Example
    -------
    output:
    {
        "1984-1-31": ["some change", "another chane"],
        ...
    }

    """
    change_log = change_log and change_log.find_parent("h2")
    change_log = change_log and change_log.find_next("ul")
    change_log = change_log and change_log.find_all("li", recursive=False)
    result = {}
    for change in change_log or []:
        day = list(change.stripped_strings)[0]
        day = re.sub(r"(?<=\d)(st|nd|rd|th)\b", '', day)
        day = datetime.strptime(day, "%B %d, %Y").date().isoformat()
        result[day] = clean_changes(change)
    return result


def unit_to_dict(data: str) -> Dict[str, Dict[str, List[str]]]:
    """
    Parse unit HTML from prismata.gamepedia.com into dict format.

    Parameters
    ----------
    data : str
        HTML for unit from prismata.gamepedia.com..

    Returns
    -------
    dict

    Example
    -------
    output:
        {
            "name": "Unit name",
            "abilities": "Ability 1. Ability 2",
            "change_history": {
                "October 31st, 1984": ["Change 1", "Change 2"],
                ...
                },
            "links": {
                "path": "/Unit_Name",
                "image": "https://image.url.com",
                "panel": "https://panel.url.com",
                },
            "position": "Middle Far Right",
        }

    """
    soup = BeautifulSoup(data, "html.parser")
    if not soup:
        logger.warning("Invalid data format for unit: %s", data)
        return {}

    abilities = soup.select_one("div.box")("div")[-1]
    change_log = soup.select_one("#Change_log")

    result = {
        "name": clean(soup.select_one("div.title")),
        "abilities": " ".join(
            clean_symbols(abilities).get_text().replace("\n", "").split()
            ),
        "change_history": clean_change_log(change_log),
        "links": {
            "path": soup.select_one("#ca-view").a.get("href"),
            "image": (soup.select_one(".thumbimage") or {}).get("src"),
            "panel": (soup.select_one("p > a.image > img") or {}).get("src"),
            },
        "position": "Middle Far Right",
        }

    logger.info("Unit processed: %s", result['name'])
    return result


def export_units_json(
        data: Dict[str, Dict[str, Union[str, int]]],
        file_name: str = "units.json"
        ) -> Dict[str, str]:
    """
    Save data into .json format/file.

    Parameters
    ----------
    data : dict
        Data to export. See Example for expected format.
    file_name : str, defaults to  "units.json"
        Path of file to save.

    Returns
    -------
    dict

    Example
    -------
    input:
        {
            "Unit Name":
                {
                    "name": "Unit name",
                    "costs": {
                        "gold": 1,
                        "energy": 0,
                        "green": 1,
                        "blue": 0,
                        "red": 1,
                        },
                    "stats": {
                        "attack": 1,
                        "health": 1,
                        },
                    "attributes": {
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
                        },
                    "links": {
                        "path": "/Unit_Name",
                        },
                    "type": 1,
                    "unit_spell": "Unit|Spell",
                },
            ...
        }

    """
    data_json = json.dumps(
        data, sort_keys=True, indent=4, separators=(",", ": "))

    with open(file_name, "w") as out_file:
        out_file.write(data_json)

    logger.info("Data exported to (JSON): %s", file_name)
    return {"message": "Success"}


def export_units_csv(
        data: Dict[str, MutableMapping[str, Mapping[str, Iterable[str]]]],
        file_name: str = "units.csv"
        ) -> Dict[str, str]:
    """
    Save data into .csv format/file.

    Parameters
    ----------
    data : dict
        Data to export. See Example for expected format.
    file_name : str, defaults to  "units.csv"
        Path of file to save.

    Returns
    -------
    dict

    Example
    -------
    input:
        {
            "Unit Name":
                {
                    "abilities": "",
                    "attributes": {
                        "blocker": false,
                        "build_time": 0,
                        "exhaust_ability": 0,
                        "exhaust_turn": 0,
                        "fragile": false,
                        "frontline": false,
                        "lifespan": 0,
                        "prompt": false,
                        "stamina": 0,
                        "supply": 0,
                    },
                    "change_history": {
                        "Month 00st, YEAR": [
                                "",
                                ...
                            ],
                        ...
                        },
                    "costs": {
                        "blue": 0,
                        "energy": 0,
                        "gold": 0,
                        "green": 0,
                        "red": 0,
                    },
                    "links": {
                        "image": "",
                        "panel": "",
                        "path": "",
                    },
                    "name": "",
                    "position": "",
                    "stats": {
                        "attack": 0,
                        "health": 0,
                    },
                    "type": 0,
                    "unit_spell": "",
                },
                ...
        }

    output:
    False, {"message": "Error message"}
    True, {"message": "Success message"}

    """
    try:
        flat_data_list = []
        for _, val in data.items():
            unit: MutableMapping[str, Any] = {}
            unit.update(val.pop("attributes"))
            unit.update(val.pop("costs"))
            unit.update(val.pop("links"))
            unit.update(val.pop("stats"))
            unit.update({
                "change_history":
                "|".join([
                    f"{day}, {' '.join(change)}"
                    for day, change in val.pop("change_history").items()
                    ])
                })
            unit.update(val)
            flat_data_list.append(unit)

        with open(file_name, "w") as out_file:
            # For ordering purposes, Using explcit list
            # instead of flat_data_list[0].keys()
            headers = [
                'name', 'supply', 'type', 'position', 'unit_spell',
                'gold', 'blue', 'red', 'green', 'energy',
                'attack', 'health', 'blocker', 'fragile',
                'frontline', 'prompt', 'lifespan', 'stamina',
                'build_time', 'exhaust_ability', 'exhaust_turn',
                'abilities', 'path', 'image', 'panel',
                'change_history',
                ]
            writer = csv.DictWriter(out_file, fieldnames=headers)
            writer.writeheader()
            for unit in flat_data_list:
                writer.writerow(unit)
    except AttributeError:
        message = "Invalid format (nested data)."
        logger.error("Error exporting CSV: %s", message)
        return {"message": message}
    except KeyError:
        message = "Invalid format (missing key)."
        logger.error("Error exporting CSV: %s", message)
        return {"message": message}

    logger.info("Data exported to (CSV): %s", file_name)
    return {"message": "Success"}


def fetch_units(
        include: Iterable[str] = ("all",), save_source: bool = False
        ) -> Dict[str, Dict[str, Union[Dict[str, int], List[str], str, int]]]:
    """
    Get information for Prismata units.

    Steps:
    1. Get general information for all units.
    2. Exclude all units not in the include parameter.
    3. Fetch details for remaining units.

    Parameters
    ----------
    include : list(str)
        Name of units to fetch. Defaults to 'all'.
    save_source : bool, defaults to False
        Wether to save the fetched html into a file on disk.

    Returns
    -------
    dict:
        HTML content.

    """
    base_url = PRISMATA_WIKI["BASE_URL"]

    logger.info(
        "Fetching\nFrom: %s\nUnits: %s\nSaving sources? %s\n",
        base_url, ','.join(include), save_source)

    # Get general information for all units
    content = get_content(
        f"{base_url}{PRISMATA_WIKI['UNITS_PATH']}", save_file=save_source)

    # Filter out units based on include param
    units: Dict[str, Any] = {
        key: val
        for key, val in unit_table_to_dict(content).items()
        if "all" in include or key in include
        }

    # Get details for each unit
    for _, value in units.items():
        delay()
        content = get_content(
            f"{base_url}{value['links']['path']}", save_file=save_source)
        unit_detail = unit_to_dict(content)
        # Flatten nested dicts (only one level)
        for key in set(value.keys()).intersection(unit_detail.keys()):
            if isinstance(unit_detail[key], dict):
                value[key].update(unit_detail.pop(key))
        value.update(unit_detail)

    logger.info("Total units fetched: %s", len(units))
    return units
