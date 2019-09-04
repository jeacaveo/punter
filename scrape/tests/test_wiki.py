""" Test for scrape.wiki module. """
import unittest
from mock import (
    MagicMock,
    patch,
    )

from scrape.wiki import (
    get_content,
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
