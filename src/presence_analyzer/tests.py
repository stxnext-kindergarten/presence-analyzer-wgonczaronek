# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
from __future__ import unicode_literals

import calendar
import datetime
import json
import os.path
import unittest

from mock import patch

from presence_analyzer import main, utils, views

TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)

TEST_DATA_WITH_HEADER_AND_FOOTER = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data_with_header_and_footer.csv'
)

INVALID_FORMAT_TEST_DATA = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'invalid_format_test_data.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {u'user_id': 10, u'name': u'User 10'})

    def test_presence_weekday_non_existent_id(self):
        """
        Test data contains ids: 10 and 11. Giving number 1 should result in 404 exit code.
        """
        response = self.client.get('/api/v1/presence_weekday/1')
        self.assertEqual(response.status_code, 404)

    def test_presence_weekday_view(self):
        """
        Test json response for user 10.
        """
        response = self.client.get('/api/v1/presence_weekday/10')

        data = json.loads(response.data)
        weekdays = utils.group_by_weekday(utils.get_data()[10])
        expected_data = [
            [calendar.day_abbr[weekday], sum(intervals)]
            for weekday, intervals in enumerate(weekdays)
            ]
        expected_data.insert(0, ['Weekday', 'Presence (s)'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_data, data)

    def test_mean_time_non_existent_id(self):
        """
        Test data contains ids: 10 and 11. Giving number 1 should result in 404 exit code.
        """
        response = self.client.get('/api/v1/mean_time_weekday/1')

        self.assertEqual(response.status_code, 404)

    def test_mean_time_weekday_view(self):
        """
        Test json response for user 10.
        """
        response = self.client.get('/api/v1/mean_time_weekday/10')

        data = json.loads(response.data)
        weekdays = utils.group_by_weekday(utils.get_data()[10])
        expected_data = [
            [calendar.day_abbr[weekday], utils.mean(intervals)]
            for weekday, intervals in enumerate(weekdays)
            ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_data, data)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        sample_date = datetime.date(2013, 9, 10)

        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_seconds_since_midnight(self):
        """
        Test time elapsed with different time set. Special case: midnight.
        """
        self.assertEqual(utils.seconds_since_midnight(datetime.time(0, 0, 0)), 0)
        self.assertEqual(utils.seconds_since_midnight(datetime.time(0, 1, 0)), 60)
        self.assertEqual(utils.seconds_since_midnight(datetime.time(0, 0, 1)), 1)
        self.assertEqual(utils.seconds_since_midnight(datetime.time(1, 0, 0)), 3600)

    def test_interval(self):
        """
        Test interval is counted correctly for two different and two same points in time.
        """
        self.assertEqual(utils.interval(datetime.time(0, 0, 0), datetime.time(0, 0, 0)), 0)
        self.assertEqual(utils.interval(datetime.time(1, 0, 0), datetime.time(0, 0, 0)), -3600)
        self.assertEqual(utils.interval(datetime.time(0, 0, 0), datetime.time(1, 1, 1)), 3661)
        self.assertEqual(utils.interval(datetime.time(0, 0, 0), datetime.time(0, 0, 50)), 50)

    def test_mean(self):
        """
        Count mean and assert it provides 3-point accuracy.
        """
        self.assertEqual(utils.mean([]), 0)
        self.assertAlmostEqual(utils.mean([1, 2]), 1.5, 3)
        self.assertAlmostEqual(utils.mean([0]), 0.0, 3)
        self.assertAlmostEqual(utils.mean([1, 2, 3, 4, 5]), 3.0, 3)

    @patch('presence_analyzer.utils.log')
    def test_invalid_data_handled(self, mocked_log):
        """
        On introduction of invalid data logger with message 'Problem with line 0' should be called.
        """
        main.app.config.update({'DATA_CSV': INVALID_FORMAT_TEST_DATA})

        with self.assertRaises(UnboundLocalError):
            utils.get_data()

        self.assertEqual(mocked_log.debug.call_count, 1)
        self.assertEqual(mocked_log.debug.call_args[0], ('Problem with line %d: ', 0))

    def test_header_and_footer_omitted(self):
        """
        The method get_data() should skip lines with more or less than 4 fields (called footers and
        headers), so it should behave as normal get_data() on file with footer and header.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_WITH_HEADER_AND_FOOTER})
        self.test_get_data()

    def test_group_by_weekday(self):
        """
        Enter sample data and check whether group serves it correctly.
        """
        data = {
            datetime.date(2017, 4, 9): {
                'start': datetime.time(12, 0, 0),
                'end': datetime.time(13, 0, 0)
            }
        }
        expected_data = [[], [], [], [], [], [], [3600]]

        data = utils.group_by_weekday(data)

        self.assertEqual(data, expected_data)


def suite():  # pragma: no cover
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
