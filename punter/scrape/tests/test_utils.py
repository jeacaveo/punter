""" Test for scrape.utils module. """
import unittest
from mock import (
    patch,
    )

from punter.scrape.utils import (
    delay,
    )


class DelayTests(unittest.TestCase):
    """ Tests for scrape.utils.delay function. """

    @patch("punter.scrape.utils.sleep")
    @patch("punter.scrape.utils.uniform")
    def test_no_params(self, random_mock, sleep_mock):
        """ Tests when no params are provided. """
        # Given
        expected_result = 1.5

        random_mock.return_value = expected_result

        # When
        result = delay()

        # Then
        self.assertEqual(result, expected_result)
        random_mock.assert_called_once_with(1, 3)
        sleep_mock.assert_called_once_with(expected_result)

    @patch("punter.scrape.utils.sleep")
    @patch("punter.scrape.utils.uniform")
    def test_params(self, random_mock, sleep_mock):
        """ Tests when params are provided. """
        # Given
        param = (2, 4)
        expected_result = 2.8

        random_mock.return_value = expected_result

        # When
        result = delay(secs=param)

        # Then
        self.assertEqual(result, expected_result)
        random_mock.assert_called_once_with(param[0], param[1])
        sleep_mock.assert_called_once_with(expected_result)
