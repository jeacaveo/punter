""" Test for scrape.config module. """
import os
import unittest
from scrape.config import (
    PRISMATA_WIKI,
    )


class VariablesTests(unittest.TestCase):
    """ Tests for scrape.config variables. """

    def test_pw_variables(self):
        """ Tests variables for PRISMATA_WIKI. """
        # Given
        expected_base_url = "https://prismata.gamepedia.com"
        expepcted_units_path = "/Unit"

        # Then
        self.assertEqual(PRISMATA_WIKI["BASE_URL"], expected_base_url)
        self.assertEqual(PRISMATA_WIKI["UNITS_PATH"], expepcted_units_path)
