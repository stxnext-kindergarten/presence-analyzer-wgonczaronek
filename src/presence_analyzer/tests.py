# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest
import testfixtures

from presence_analyzer import main, views, utils

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

    def test_presence_weekday_returns_404_on_no_user_id(self):
        """
        Test data contains ids: 10 and 11. Giving number -1 should result in 404 exit code
        Test status code is 404
        """
        response = self.client.get('/api/v1/presence_weekday/1')
        self.assertEqual(response.status_code, 404)

    def test_presence_weekday_view(self):
        """
        Test json response for user 10
        From test_data.csv:
        2013-09-10: Tuesday 30047 seconds
        2013-09-11: Wednesday 24465 seconds
        2013-09-12: Thursday 23705 seconds
        """
        response = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Change to dict for easier checks
        data = dict(data)
        self.assertEqual(len(data), 8)
        self.assertEqual(data[u'Weekday'], u'Presence (s)')
        self.assertEqual(data[u'Mon'], 0)
        self.assertEqual(data[u'Tue'], 30047)
        self.assertEqual(data[u'Wed'], 24465)
        self.assertEqual(data[u'Thu'], 23705)
        self.assertEqual(data[u'Fri'], 0)
        self.assertEqual(data[u'Sat'], 0)
        self.assertEqual(data[u'Sun'], 0)

    def test_mean_time_weekday_returns_404_on_no_user_id(self):
        """
        Test data contains ids: 10 and 11. Giving number -1 should result in 404 exit code
        Test status code is 404
        """
        response = self.client.get('/api/v1/mean_time_weekday/1')
        self.assertEqual(response.status_code, 404)

    def test_mean_time_weekday_view(self):
        """
        Test json response for user 10
        From test_data.csv:
        2013-09-10: Tuesday 30047 seconds
        2013-09-11: Wednesday 24465 seconds
        2013-09-12: Thursday 23705 seconds
        """
        response = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Change to dict for easier checks
        data = dict(data)
        self.assertEqual(len(data), 7)
        self.assertEqual(data[u'Mon'], 0)
        self.assertEqual(data[u'Tue'], 30047)
        self.assertEqual(data[u'Wed'], 24465)
        self.assertEqual(data[u'Thu'], 23705)
        self.assertEqual(data[u'Fri'], 0)
        self.assertEqual(data[u'Sat'], 0)
        self.assertEqual(data[u'Sun'], 0)


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
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_seconds_since_midnight_return_correct_time(self):
        """
        Test time elapsed with different time set. Special case: midnight.
        """
        midnight_time = datetime.time(0, 0, 0)
        second_after_midnight = datetime.time(0, 0, 1)
        minute_after_midnight = datetime.time(0, 1, 0)
        hour_after_midnight = datetime.time(1, 0, 0)
        self.assertEqual(utils.seconds_since_midnight(midnight_time), 0)
        self.assertEqual(utils.seconds_since_midnight(second_after_midnight), 1)
        self.assertEqual(utils.seconds_since_midnight(minute_after_midnight), 60)
        self.assertEqual(utils.seconds_since_midnight(hour_after_midnight), 3600)

    def test_interval_returns_correct_interval(self):
        """
        Test interval
        """
        start = datetime.time(0, 0, 0)
        stop = datetime.time(1, 1, 1)
        self.assertEqual(utils.interval(start, stop), 3661)

    def test_mean_returns_zero_for_empty_list(self):
        """
        Mean checks whether provided list is empty and returns 0 if so.
        """
        self.assertEqual(utils.mean([]), 0)

    def test_mean_within_1_percent_accuracy_for_non_empty_list(self):
        """
        Count mean and assert it provides 3-point accuracy.
        """
        items = [1, 2]
        self.assertAlmostEqual(utils.mean(items), 1.5, 3)

    def test_invalid_data_exception_is_caught(self):
        """
        Captures log and checks whether 'Problem with line' message is found.
        """
        with testfixtures.LogCapture() as log_capture:

            main.app.config.update({'DATA_CSV': INVALID_FORMAT_TEST_DATA})
            try:
                utils.get_data()
            except UnboundLocalError:
                pass
            main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
            self.assertTrue(any(filter(lambda x: 'Problem with line' in x.msg, log_capture.records)))

    def test_header_and_footer_is_omitted(self):
        """
        Works exactly as test_get_data, however, the file it works on contains footers and headers
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_WITH_HEADER_AND_FOOTER})
        self.test_get_data()
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def test_group_by_weekday(self):
        """
        Enter sample data and check whether group serves it correctly.
        The data contains one entry set to Sunday (for easier iterating) with one
        hour interval.
        """
        # Sunday with one hour interval
        data = {
            datetime.date(2017, 4, 9): {
                'start': datetime.time(12, 0, 0),
                'end': datetime.time(13, 0, 0)
            }
        }

        weekday_result = utils.group_by_weekday(data)
        # From Monday to Saturday no data has been entered, so there should be
        # empty lists
        for i in range(6):
            self.assertEqual(len(weekday_result[i]), 0)
        # Ensure there is one entry for Sunday
        self.assertEqual(len(weekday_result[6]), 1)
        # Ensure it contains 1 hour interval
        self.assertEqual(weekday_result[6][0], 3600)


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
