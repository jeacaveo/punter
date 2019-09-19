""" Module for scraping prismata.gamepedia.com """
import csv
import json
import requests

from bs4 import BeautifulSoup

from scrape.config import PRISMATA_WIKI
from scrape.utils import delay


# Mapping from symbol titles into str representation
TITLE_SYMBOL_MAP = {
    "Gold": "",
    "Energy": "E",
    "Green resource": "G",
    "Blue resource": "B",
    "Red resource": "R",
    "Attack": "X",
    "Ability": "Click",
    }


def get_content(url, file_name=""):
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
        if file_name:
            save_path = f"{PRISMATA_WIKI['SAVE_PATH']}{file_name}"
            with open(save_path, "w") as out_file:
                out_file.write(str(response.content))
        return response.content
    return ""


def clean(item, cast=str):
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
    if item.div:
        item = item.div
    return cast(item.text.strip())


def unit_table_to_dict(data):
    """
    Parse HTML unit table from prismata.gamepedia.com into dict format.

    Parameters
    ----------
    data : str
        HTML table for unit list from prismata.gamepedia.com..

    Returns
    -------
    tuple(bool, dict)

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

    Example
    -------
    False, {"message": "Error message"}
    True, {output}

    """
    soup = BeautifulSoup(data, "html.parser")

    if not soup:
        return False, {"message": "Invalid format."}

    result = {}
    for row in soup.table("tr"):
        unit = row("td")
        if unit:
            name = clean(unit[0])
            result[name] = {
                "name": name,
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
    return True, result


def clean_symbols(element):
    """
    Change symbol links into text..

    Parameters
    ----------
    item : bs4.element.Tag
        Tag object from BeautifulSoup4 library.

    Returns
    -------
    bs4.element.Tag
        Returns the same element provided as parameter,
        but with all symbol links replaced.

    """
    for icon in element("a"):
        title = icon.get("title")
        symbol = TITLE_SYMBOL_MAP.get(title, title)
        icon.replace_with(symbol)
    return element


def clean_changes(item):
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
    for element in item.ul("li"):
        element = clean_symbols(element)
        content = element.get_text().replace("\n", "")
        clean_values.append(" ".join(content.split()))
    return clean_values


def unit_to_dict(data):
    """
    Parse unit HTML from prismata.gamepedia.com into dict format.

    Parameters
    ----------
    data : str
        HTML for unit from prismata.gamepedia.com..

    Returns
    -------
    dict
        Unit information

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
        return False, {"message": "Invalid format."}

    abilities = soup.select_one("div.box")("div")[2]
    change_log = soup.select_one("#Change_log").find_parent(
        "h2").find_next("ul").find_all("li", recursive=False)

    result = {
        "name": clean(soup.select_one("div.title")),
        "abilities": " ".join(
            clean_symbols(abilities).get_text().replace("\n", "").split()),
        "change_history": {
            list(change.stripped_strings)[0]:  # day
            clean_changes(change)  # changes list
            for change in change_log
            },
        "links": {
            "path": soup.select_one("#ca-view").a.get("href"),
            "image": soup.select_one(".thumbimage").get("src"),
            "panel": soup.select_one("p > a.image > img").get("src"),
            },
        "position": "Middle Far Right",
        }
    return True, result


def export_units_json(data, file_name="units.json"):
    """
    Save data into .json format/file.

    Parameters
    ----------
    data : dict
        Data to export. See Example for expected format.

    Returns
    -------
    tuple(bool, dict)

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

    output:
    False, {"message": "Error message"}
    True, {"message": "Success message"}

    """
    data_json = json.dumps(
        data, sort_keys=True, indent=4, separators=(",", ": "))

    with open(file_name, "w") as out_file:
        out_file.write(data_json)
    return True, {"message": "Success"}


def export_units_csv(data, file_name="units.csv"):
    """
    Save data into .csv format/file.

    Parameters
    ----------
    data : dict
        Data to export. See Example for expected format.

    Returns
    -------
    tuple(bool, dict)

    Example
    -------
    input:
        {
            "Unit Name":
                {
                    "path": "/Unit_Name",
                    "costs": {
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

    output:
    False, {"message": "Error message"}
    True, {"message": "Success message"}

    """
    try:
        flat_data_list = []
        for key, val in data.items():
            unit = {"name": key}
            unit.update(val.pop("costs"))
            unit.update(val)
            flat_data_list.append(unit)

        with open(file_name, "w") as out_file:
            headers = flat_data_list[0].keys()
            writer = csv.DictWriter(out_file, fieldnames=headers)
            writer.writeheader()
            for unit in flat_data_list:
                writer.writerow(unit)
    except IndexError:
        return False, {"message": "No data provided."}
    except AttributeError:
        return False, {"message": "Invalid format (nested data)."}
    except KeyError:
        return False, {"message": "Invalid format (missing key)."}
    return True, {"message": "Success"}


def fetch_units(include=["all"], save_source=""):
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

    Returns
    -------
    tuple(bool, dict):
        HTML content.

    """
    base_url = PRISMATA_WIKI["BASE_URL"]

    # Get general information for all units
    content = get_content(
        f"{base_url}{PRISMATA_WIKI['UNITS_PATH']}",
        file_name=save_source and PRISMATA_WIKI["UNITS_PATH"])
    if not content:
        return False, {"message": "Invalid URL configuration."}

    is_valid, all_units = unit_table_to_dict(content)
    if not is_valid:
        return is_valid, all_units

    # Filter out units based on include param
    all_units = {
        key: val
        for key, val in all_units.items()
        if "all" in include or key in include
        }

    # Get details for each unit
    for name, value in all_units.items():
        delay()
        content = get_content(
            f"{base_url}{value['links']['path']}",
            file_name=save_source and value["links"]["path"])
        valid_detail, unit_detail = unit_to_dict(content)
        if valid_detail:
            # Flatten nested dicts (only one level)
            for key in set(value.keys()).intersection(unit_detail.keys()):
                if isinstance(unit_detail[key], dict):
                    value[key].update(unit_detail.pop(key))
            value.update(unit_detail)

    return is_valid, all_units
