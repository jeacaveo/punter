""" Test for scrape.wiki module. """
import json
import os
import unittest
from mock import (
    call,
    MagicMock,
    patch,
    )

from punter.scrape import config
from punter.scrape.wiki import (
    clean,
    clean_changes,
    clean_symbols,
    export_units_csv,
    export_units_json,
    fetch_units,
    get_content,
    unit_to_dict,
    unit_table_to_dict,
    )


class GetContentTests(unittest.TestCase):
    """ Tests for scrape.wiki.get_content. """

    @patch("punter.scrape.wiki.requests.get")
    def test_error(self, requests_mock):
        """ Tests response when request is not successfull. """
        # Given
        url = "http://example.com"
        expected_result = ""

        requests_mock.return_value = MagicMock(status_code=400)

        # When
        result = get_content(url)

        # Then
        self.assertEqual(result, expected_result)
        requests_mock.assert_called_once_with(url)

    @patch("punter.scrape.wiki.requests.get")
    def test_success(self, requests_mock):
        """ Tests response when request is successfull. """
        # Given
        url = "http://example.com"
        expected_result = "<html></html>"

        requests_mock.return_value = MagicMock(
            status_code=200,
            content=expected_result,
            )

        # When
        result = get_content(url)

        # Then
        self.assertEqual(result, expected_result)
        requests_mock.assert_called_once_with(url)

    @patch("punter.scrape.wiki.BeautifulSoup")
    @patch("builtins.open")
    @patch("punter.scrape.wiki.requests.get")
    def test_save(self, requests_mock, open_mock, soup_mock):
        """ Tests saving of content when request is successfull. """
        # Given
        url = "http://example.com"
        expected_result = "<html></html>"

        requests_mock.return_value = MagicMock(
            status_code=200,
            content=expected_result,
            )
        open_mock.return_value = open_mock
        soup_mock.return_value = soup_mock
        soup_mock.prettify.return_value = expected_result

        # When
        result = get_content(url, save_file=True)

        # Then
        self.assertEqual(result, expected_result)
        requests_mock.assert_called_once_with(url)
        open_mock.assert_has_calls([
            call(url, "w"),
            call.__enter__(),
            call.__enter__().write(expected_result),
            call.__exit__(None, None, None),
            ])
        soup_mock.assert_has_calls([
            call(expected_result, "html.parser"),
            call.prettify(),
            ])

    @patch("builtins.open")
    @patch("os.path.isfile")
    @patch("punter.scrape.wiki.requests.get")
    def test_read_from_file(self, requests_mock, isfile_mock, open_mock):
        """ Tests content when file exists (instead of calling url). """
        # Given
        path = "/path/to/file.html"
        expected_result = "<html></html>"

        isfile_mock.return_value = True
        open_mock.return_value = expected_result

        # When
        result = get_content(path)

        # Then
        self.assertEqual(result, expected_result)
        self.assertFalse(requests_mock.called)
        open_mock.assert_called_once_with(path, "r")


class CleanTests(unittest.TestCase):
    """ Tests for scrape.wiki.clean. """

    def test_div(self):
        """ Tests result when input data has a div value. """
        # Given
        data = MagicMock(div=MagicMock(text="abc"))
        expected_result = "abc"

        # When
        result = clean(data)

        # Then
        self.assertEqual(result, expected_result)

    def test_int(self):
        """ Tests result when input data is a string number. """
        # Given
        data = MagicMock(div=None, text=" \n 999 \n ")
        expected_result = 999

        # When
        result = clean(data, int)

        # Then
        self.assertEqual(result, expected_result)


class UnitTableToDictTests(unittest.TestCase):
    """ Tests for scrape.wiki.unit_table_to_dict. """

    @patch("punter.scrape.wiki.BeautifulSoup")
    def test_invalid_input_format(self, soup_mock):
        """ Tests result when input data has invalid format. """
        # Given
        data = ""
        expected_result = False, {"message": "Invalid format."}

        soup_mock.return_value = None

        # When
        result = unit_table_to_dict(data)

        # Then
        self.assertEqual(result, expected_result)
        soup_mock.assert_called_once_with(data, "html.parser")

    @patch("punter.scrape.wiki.BeautifulSoup")
    def test_empty_rows(self, soup_mock):
        """ Tests result when input data has valid format but no rows. """
        # Given
        data = "<html><table></table></html>"
        expected_dict = {}
        expected_result = True, expected_dict

        row_mock = MagicMock()
        soup_mock.return_value = MagicMock()
        soup_mock.return_value.table.return_value = [row_mock]
        row_mock.return_value = None

        # When
        result = unit_table_to_dict(data)

        # Then
        self.assertEqual(result, expected_result)
        soup_mock.assert_called_once_with(data, "html.parser")
        soup_mock.return_value.table.assert_called_once_with("tr")
        row_mock.assert_called_once_with("td")

    @patch("punter.scrape.wiki.clean")
    @patch("punter.scrape.wiki.BeautifulSoup")
    def test_valid_input_format(self, soup_mock, clean_mock):
        """ Tests result when input data has valid format. """
        # Given
        data = "<html><table>...valid rows/columns...</table></html>"
        expected_dict = {
            "name": {
                "name": "name",
                "costs": {
                    "gold": 3,
                    "energy": 4,
                    "green": 5,
                    "blue": 6,
                    "red": 7,
                    },
                "stats": {
                    "attack": 15,
                    "health": 10,
                    },
                "attributes": {
                    "supply": 8,
                    "frontline": True,
                    "fragile": False,
                    "blocker": True,
                    "prompt": False,
                    "stamina": 16,
                    "lifespan": 19,
                    "build_time": 9,
                    "exhaust_turn": 17,
                    "exhaust_ability": 18,
                    },
                "links": {
                    "path": "/name",
                    },
                "type": 1,
                "unit_spell": "unit/spell",
                }
            }
        expected_result = True, expected_dict

        row_mock = MagicMock()
        soup_mock.return_value = MagicMock()
        soup_mock.return_value.table.return_value = [row_mock]
        row_mock.return_value = [
            MagicMock(a={"href": "/name"}),
            "1",
            "unit/spell",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "True",
            "",
            "True",
            "",
            "15",
            "16",
            "17",
            "18",
            "19",
            ]
        clean_mock.side_effect = [
            "name",
            3,
            4,
            5,
            6,
            7,
            "15",
            10,
            8,
            True,
            False,
            True,
            False,
            16,
            19,
            9,
            17,
            18,
            1,
            "unit/spell",
            ]

        # When
        result = unit_table_to_dict(data)

        # Then
        self.assertEqual(result, expected_result)
        soup_mock.assert_called_once_with(data, "html.parser")
        soup_mock.return_value.table.assert_called_once_with("tr")
        row_mock.assert_called_once_with("td")
        clean_mock.assert_has_calls([])


class ExportUnitsJsonTests(unittest.TestCase):
    """ Tests for scrape.wiki.export_units_json. """

    def setUp(self):
        self.file_name = "units.json.test"

    @patch("builtins.open")
    def test_success(self, open_mock):
        """ Tests json file is saved when valid format is provided. """
        # Given
        data = {
            "name": {
                "name": "name",
                "costs": {
                    "gold": 3,
                    "energy": 4,
                    "green": 5,
                    "blue": 6,
                    "red": 7,
                    },
                "stats": {
                    "attack": 15,
                    "health": 10,
                    },
                "attributes": {
                    "supply": 8,
                    "frontline": True,
                    "fragile": False,
                    "blocker": True,
                    "prompt": False,
                    "stamina": 16,
                    "lifespan": 19,
                    "build_time": 9,
                    "exhaust_turn": 17,
                    "exhaust_ability": 18,
                    },
                "links": {
                    "path": "/name",
                    },
                "type": 1,
                "unit_spell": "unit/spell",
                }
            }
        json_data = json.dumps(
            data, sort_keys=True, indent=4, separators=(",", ": "))
        expected_result = True, {"message": "Success"}

        open_mock.return_value = open_mock

        # When
        result = export_units_json(data, file_name=self.file_name)

        # Then
        self.assertEqual(result, expected_result)
        open_mock.assert_has_calls([
            call(self.file_name, "w"),
            call.__enter__(),
            call.__enter__().write(json_data),
            call.__exit__(None, None, None),
            ])


class ExportUnitsCsvTests(unittest.TestCase):
    """ Tests for scrape.wiki.export_units_csv. """

    def setUp(self):
        self.file_name = "units.csv.test"

    def tearDown(self):
        if os.path.isfile(self.file_name):
            os.remove(self.file_name)

    def test_format_attribute(self):
        """ Tests error when invalid data format is provided. """
        # Given
        data = {"bad": "wrong"}
        expected_result = False, {"message": "Invalid format (nested data)."}

        # When
        result = export_units_csv(data, file_name=self.file_name)

        # Then
        self.assertEqual(result, expected_result)
        self.assertFalse(os.path.isfile(self.file_name))

    def test_invalid_key(self):
        """ Tests error when invalid data format is provided. """
        # Given
        data = {"bad": {}}
        expected_result = False, {"message": "Invalid format (missing key)."}

        # When
        result = export_units_csv(data, file_name=self.file_name)

        # Then
        self.assertEqual(result, expected_result)
        self.assertFalse(os.path.isfile(self.file_name))

    def test_success(self):
        """ Tests csv file is saved when valid format is provided. """
        # Given
        data = {
            "name": {
                "name": "name",
                "costs": {
                    "gold": 3,
                    "energy": 4,
                    "green": 5,
                    "blue": 6,
                    "red": 7,
                    },
                "stats": {
                    "attack": 15,
                    "health": 10,
                    },
                "attributes": {
                    "supply": 8,
                    "frontline": True,
                    "fragile": False,
                    "blocker": True,
                    "prompt": False,
                    "stamina": 16,
                    "lifespan": 19,
                    "build_time": 9,
                    "exhaust_turn": 17,
                    "exhaust_ability": 18,
                    },
                "links": {
                    "path": "/name",
                    },
                "type": 1,
                "unit_spell": "unit/spell",
                "change_history": {
                    "May 1st, 1984": ["Change1", "Change2"],
                    },
                }
            }
        expected_result = True, {"message": "Success"}

        # When
        result = export_units_csv(data, file_name=self.file_name)

        # Then
        self.assertEqual(result, expected_result)
        self.assertTrue(os.path.isfile(self.file_name))


class CleanSymbolsTests(unittest.TestCase):
    """ Tests for scrape.wiki.clean_symbols. """

    def test_no_links(self):
        """ Tests result when input data has no links (a tag). """
        # Given
        tag_obj = MagicMock()
        expected_result = tag_obj

        tag_obj.return_value = []

        # When
        result = clean_symbols(tag_obj)

        # Then
        self.assertEqual(result, expected_result)
        tag_obj.assert_called_once_with("a")

    def test_links(self):
        """ Tests result when input data has links (a tag). """
        # Given
        tag_obj = MagicMock()
        icon_obj = MagicMock()
        expected_result = tag_obj

        tag_obj.return_value = [icon_obj]
        icon_obj.get.return_value = "Attack"

        # When
        result = clean_symbols(tag_obj)

        # Then
        self.assertEqual(result, expected_result)
        tag_obj.assert_called_once_with("a")
        icon_obj.get.assert_called_once_with("title")
        icon_obj.replace_with.assert_called_once_with("X")


class CleanChangesTests(unittest.TestCase):
    """ Tests for scrape.wiki.clean_changes. """

    def test_no_changes(self):
        """ Tests result when input data has no changes. """
        # Given
        tag_obj = MagicMock()
        expected_result = []

        tag_obj.ul.return_value = []

        # When
        result = clean_changes(tag_obj)

        # Then
        self.assertEqual(result, expected_result)
        tag_obj.ul.assert_called_once_with("li")

    @patch("punter.scrape.wiki.clean_symbols")
    def test_changes(self, symbols_mock):
        """ Tests result when input data has changes. """
        # Given
        tag_obj = MagicMock()
        element_obj = MagicMock()
        expected_result = ["some change"]

        tag_obj.ul.return_value = [element_obj]
        symbols_mock.return_value = element_obj
        element_obj.get_text.return_value = " \n some\n change \n "

        # When
        result = clean_changes(tag_obj)

        # Then
        self.assertEqual(result, expected_result)
        tag_obj.ul.assert_called_once_with("li")
        symbols_mock.assert_called_once_with(element_obj)
        element_obj.get_text.assert_called_once_with()


class UnitToDictTests(unittest.TestCase):
    """ Tests for scrape.wiki.unit_to_dict. """

    @patch("punter.scrape.wiki.BeautifulSoup")
    def test_invalid_input_format(self, soup_mock):
        """ Tests result when input data has invalid format. """
        # Given
        data = ""
        expected_result = False, {"message": "Invalid format."}

        soup_mock.return_value = None

        # When
        result = unit_to_dict(data)

        # Then
        self.assertEqual(result, expected_result)
        soup_mock.assert_called_once_with(data, "html.parser")

    @patch("punter.scrape.wiki.clean_changes")
    @patch("punter.scrape.wiki.clean_symbols")
    @patch("punter.scrape.wiki.clean")
    @patch("punter.scrape.wiki.BeautifulSoup")
    def test_valid_input_format(
            self, soup_mock, clean_mock, symbols_mock, changes_mock):
        """ Tests result when input data has valid format. """
        # Given
        data = "<html><table>...valid structure...</table></html>"
        name = "Unit Name"
        path = "/Unit_Name"
        image_url = "https://image.url.com"
        panel_url = "https://panel.url.com"
        abilities = ["Ability1. Ability 2"]
        expected_dict = {
            "name": name,
            "abilities": abilities[-1],
            "change_history": {
                "day 1": ["change1", "change2"],
                "day 2": ["change3"],
                },
            "links": {
                "path": path,
                "image": image_url,
                "panel": panel_url,
                },
            "position": "Middle Far Right",
            }
        expected_result = True, expected_dict

        div_box = MagicMock()
        change_log = MagicMock()
        changes1 = MagicMock(stripped_strings=("day 1",))
        changes2 = MagicMock(stripped_strings=("day 2",))
        ca_view = MagicMock(a={"href": path})
        thumbimage = {"src": image_url}
        panelimage = {"src": panel_url}
        soup_mock.return_value = soup_mock
        soup_mock.select_one.side_effect = [
            div_box,
            change_log,
            name,
            ca_view,
            thumbimage,
            panelimage,
            ]
        clean_mock.return_value = name
        div_box.return_value = abilities
        symbols_mock.return_value = symbols_mock
        symbols_mock.get_text.return_value = abilities[-1]
        change_log.return_value = change_log
        change_log.find_parent.return_value = change_log
        change_log.find_next.return_value = change_log
        change_log.find_all.return_value = [changes1, changes2]
        changes_mock.side_effect = [
            ["change1", "change2"],
            ["change3"],
            ]

        # When
        result = unit_to_dict(data)

        # Then
        self.assertEqual(result, expected_result)
        soup_mock.assert_called_once_with(data, "html.parser")
        soup_mock.select_one.assert_has_calls([
            call("div.box"),
            call("#Change_log"),
            call("div.title"),
            call("#ca-view"),
            call(".thumbimage"),
            call("p > a.image > img"),
            ])
        div_box.assert_called_once_with("div")
        change_log.assert_has_calls([
            call.__bool__(),
            call.find_parent("h2"),
            call.__bool__(),
            call.find_next("ul"),
            call.__bool__(),
            call.find_all("li", recursive=False),
            ])
        clean_mock.assert_called_once_with(name)
        symbols_mock.assert_has_calls([
            call(abilities[-1]),
            call.get_text(),
            ])


class FetchUnitsTests(unittest.TestCase):
    """ Tests for scrape.wiki.fetch_units. """

    def setUp(self):
        self.base_url = config.PRISMATA_WIKI["BASE_URL"]

    @patch("punter.scrape.wiki.get_content")
    def test_invalid_url_config(self, content_mock):
        """ Tests invalid URL configuration. """
        # Given
        expected_url = f"{self.base_url}{config.PRISMATA_WIKI['UNITS_PATH']}"
        expected_result = False, {"message": "Invalid URL configuration."}

        content_mock.return_value = ""

        # When
        result = fetch_units()

        # Then
        self.assertEqual(result, expected_result)
        content_mock.assert_called_once_with(expected_url, save_file=False)

    @patch("punter.scrape.wiki.unit_table_to_dict")
    @patch("punter.scrape.wiki.get_content")
    def test_invalid_html_all_units(self, content_mock, table_mock):
        """ Tests invalid HTML fetch for all units. """
        # Given
        expected_url = f"{self.base_url}{config.PRISMATA_WIKI['UNITS_PATH']}"
        expected_data = "invalid content"
        expected_result = False, {"message": "error"}

        content_mock.return_value = expected_data
        table_mock.return_value = expected_result

        # When
        result = fetch_units()

        # Then
        self.assertEqual(result, expected_result)
        content_mock.assert_called_once_with(expected_url, save_file=False)
        table_mock.assert_called_once_with(expected_data)

    @patch("punter.scrape.wiki.unit_to_dict")
    @patch("punter.scrape.wiki.delay")
    @patch("punter.scrape.wiki.unit_table_to_dict")
    @patch("punter.scrape.wiki.get_content")
    def test_no_details(self, content_mock, table_mock, delay_mock, unit_mock):
        """ Tests fetch no details for units. """
        # Given
        expected_url = f"{self.base_url}{config.PRISMATA_WIKI['UNITS_PATH']}"
        expected_raw_data = "some data"
        expected_data = {
            "unit1": {"key1": "val1", "links": {"path": "/unit1"}},
            "unit2": {"key3": "val3", "links": {"path": "/unit2"}},
            }
        expected_result = True, expected_data

        content_mock.side_effect = [
            expected_raw_data,
            "",
            "",
            ]
        table_mock.return_value = True, expected_data
        unit_mock.side_effect = [
            (False, {}),
            (False, {}),
            ]

        # When
        result = fetch_units()

        # Then
        self.assertEqual(result, expected_result)
        content_mock.assert_has_calls([
            call(expected_url, save_file=False),
            call(
                f"{self.base_url}{expected_data['unit1']['links']['path']}",
                save_file=False),
            call(
                f"{self.base_url}{expected_data['unit2']['links']['path']}",
                save_file=False),
            ])
        table_mock.assert_called_once_with(expected_raw_data)
        delay_mock.assert_has_calls([
            call(),
            call(),
            ])
        unit_mock.assert_has_calls([
            call(""),
            call(""),
            ])

    @patch("punter.scrape.wiki.unit_to_dict")
    @patch("punter.scrape.wiki.delay")
    @patch("punter.scrape.wiki.unit_table_to_dict")
    @patch("punter.scrape.wiki.get_content")
    def test_details_all(
            self, content_mock, table_mock, delay_mock, unit_mock):
        """ Tests fetch details for all units. """
        # Given
        expected_url = f"{self.base_url}{config.PRISMATA_WIKI['UNITS_PATH']}"
        expected_raw_table = "raw table"
        expected_raw_unit1 = "raw unit 1"
        expected_raw_unit2 = "raw unit 2"
        expected_table_data = {
            "unit1": {
                "key1": "val1",
                "links": {"path": "/unit1"},
                },
            "unit2": {
                "key3": "val3",
                "links": {"path": "/unit2"},
                },
            }
        expected_unit1 = {
            "name": "unit1",
            "keyX": "extra val 1",
            "links": {"valW": "sub3"},
            }
        expected_unit2 = {
            "name": "unit2",
            "keyZ": "extra val 2",
            "links": {"valY": "sub4"},
            }
        expected_data = {
            "unit1": {
                "key1": "val1",
                "links": {"path": "/unit1", "valW": "sub3"},
                "name": "unit1",
                "keyX": "extra val 1",
                },
            "unit2": {
                "key3": "val3",
                "links": {"path": "/unit2", "valY": "sub4"},
                "name": "unit2",
                "keyZ": "extra val 2",
                },
            }
        expected_result = True, expected_data

        content_mock.side_effect = [
            expected_raw_table,
            expected_raw_unit1,
            expected_raw_unit2,
            ]
        table_mock.return_value = True, expected_table_data
        unit_mock.side_effect = [
            (True, expected_unit1),
            (True, expected_unit2),
            ]

        # When
        result = fetch_units()

        # Then
        self.maxDiff = None
        self.assertEqual(result, expected_result)
        content_mock.assert_has_calls([
            call(expected_url, save_file=False),
            call(
                f"{self.base_url}{expected_data['unit1']['links']['path']}",
                save_file=False),
            call(
                f"{self.base_url}{expected_data['unit2']['links']['path']}",
                save_file=False),
            ])
        table_mock.assert_called_once_with(expected_raw_table)
        delay_mock.assert_has_calls([
            call(),
            call(),
            ])
        unit_mock.assert_has_calls([
            call(expected_raw_unit1),
            call(expected_raw_unit2),
            ])

    @patch("punter.scrape.wiki.unit_to_dict")
    @patch("punter.scrape.wiki.delay")
    @patch("punter.scrape.wiki.unit_table_to_dict")
    @patch("punter.scrape.wiki.get_content")
    def test_details_some(
            self, content_mock, table_mock, delay_mock, unit_mock):
        """ Tests fetch details for specific units. """
        # Given
        expected_url = f"{self.base_url}{config.PRISMATA_WIKI['UNITS_PATH']}"
        expected_raw_table = "raw table"
        expected_raw_unit1 = "raw unit 2"
        expected_table_data = {
            "unit1": {
                "key1": "val1",
                "links": {"path": "/unit1"},
                },
            "unit2": {
                "key3": "val3",
                "links": {"path": "/unit2"},
                },
            }
        expected_unit1 = {
            "name": "unit2",
            "keyZ": "extra val 2",
            "links": {"valY": "sub4"},
            }
        expected_data = {
            "unit2": {
                "key3": "val3",
                "links": {"path": "/unit2", "valY": "sub4"},
                "name": "unit2",
                "keyZ": "extra val 2",
                },
            }
        expected_result = True, expected_data

        content_mock.side_effect = [
            expected_raw_table,
            expected_raw_unit1,
            ]
        table_mock.return_value = True, expected_table_data
        unit_mock.side_effect = [
            (True, expected_unit1),
            ]

        # When
        result = fetch_units(include=["unit2"])

        # Then
        self.maxDiff = None
        self.assertEqual(result, expected_result)
        content_mock.assert_has_calls([
            call(expected_url, save_file=False),
            call(
                f"{self.base_url}{expected_data['unit2']['links']['path']}",
                save_file=False),
            ])
        table_mock.assert_called_once_with(expected_raw_table)
        delay_mock.assert_called_once_with()
        unit_mock.assert_called_once_with(expected_raw_unit1)
