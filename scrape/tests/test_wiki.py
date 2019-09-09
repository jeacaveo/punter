""" Test for scrape.wiki module. """
import os
import unittest
from mock import (
    MagicMock,
    patch,
    )

from scrape.wiki import (
    clean,
    export_units_csv,
    export_units_json,
    get_content,
    unit_table_to_dict,
    )


class GetContentTests(unittest.TestCase):
    """ Tests for scrape.wiki.get_content. """

    @patch("scrape.wiki.requests.get")
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

    @patch("scrape.wiki.requests.get")
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

    @patch("scrape.wiki.BeautifulSoup")
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

    @patch("scrape.wiki.BeautifulSoup")
    def test_empty_rows(self, soup_mock):
        """ Tests result when input data has valid format but now rows. """
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

    @patch("scrape.wiki.clean")
    @patch("scrape.wiki.BeautifulSoup")
    def test_valid_input_format(self, soup_mock, clean_mock):
        """ Tests result when input data has valid format. """
        # Given
        data = "<html><table>...valid rows/columns...</table></html>"
        expected_dict = {
            "name": {
                "url_path": "/name",
                "cost": {
                    "gold": 3,
                    "energy": 4,
                    "green": 5,
                    "blue": 6,
                    "red": 7,
                    },
                "attack": 15,
                "health": 10,
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
            "name",  # For some reason index 0 needs to be a the end?
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

    def tearDown(self):
        if os.path.isfile(self.file_name):
            os.remove(self.file_name)

    def test_success(self):
        """ Tests json file is saved when valid format is provided. """
        # Given
        data = {
            "name": {
                "url_path": "/name",
                "cost": {
                    "gold": 3,
                    "energy": 4,
                    "green": 5,
                    "blue": 6,
                    "red": 7,
                    },
                "attack": 15,
                "health": 10,
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
                "type": 1,
                "unit_spell": "unit/spell",
                }
            }
        expected_result = True, {"message": "Success"}

        # When
        result = export_units_json(data, file_name=self.file_name)

        # Then
        self.assertEqual(result, expected_result)
        self.assertTrue(os.path.isfile(self.file_name))


class ExportUnitsCsvTests(unittest.TestCase):
    """ Tests for scrape.wiki.export_units_csv. """

    def setUp(self):
        self.file_name = "units.csv.test"

    def tearDown(self):
        if os.path.isfile(self.file_name):
            os.remove(self.file_name)

    def test_format_index(self):
        """ Tests error when empty data is provided. """
        # Given
        data = {}
        expected_result = False, {"message": "No data provided."}

        # When
        result = export_units_csv(data, file_name=self.file_name)

        # Then
        self.assertEqual(result, expected_result)
        self.assertTrue(os.path.isfile(self.file_name))

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
                "url_path": "/name",
                "cost": {
                    "gold": 3,
                    "energy": 4,
                    "green": 5,
                    "blue": 6,
                    "red": 7,
                    },
                "attack": 15,
                "health": 10,
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
                "type": 1,
                "unit_spell": "unit/spell",
                }
            }
        expected_result = True, {"message": "Success"}

        # When
        result = export_units_csv(data, file_name=self.file_name)

        # Then
        self.assertEqual(result, expected_result)
        self.assertTrue(os.path.isfile(self.file_name))
