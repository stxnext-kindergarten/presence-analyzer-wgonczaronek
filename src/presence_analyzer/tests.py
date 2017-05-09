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
import locale

from mock import patch
from mock.mock import Mock

from presence_analyzer import main, utils, views
from presence_analyzer.cronjobs import download_xml

TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data', 'test_data.csv'
)

TEST_DATA_WITH_HEADER_AND_FOOTER = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data',
    'test_data_with_header_and_footer.csv'
)

INVALID_FORMAT_TEST_DATA = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data',
    'invalid_format_test_data.csv'
)

TEST_USERS_XML_FILE = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data', 'test_users.xml'
)

locale.setlocale(locale.LC_COLLATE, ('en', 'utf-8'))


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
        utils._cache = {}
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
        assert resp.headers['Location'].endswith('/presence_weekday/')

    def test_api_users(self):
        """
        Test users listing. The request for users should return result sorted by names with users
        with not found names in the end, so: Adam A, Zenon Z, User 1, User 12.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 4)
        self.assertDictEqual(data[0], {'user_id': 11, 'name': 'Maciej D.'})
        self.assertDictEqual(data[1], {'user_id': 10, 'name': 'Maciej Z.'})
        self.assertDictEqual(data[2], {'user_id': 13, 'name': 'User 13'})
        self.assertDictEqual(data[3], {'user_id': 130, 'name': 'User 130'})

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

    def test_start_end_weekday_view(self):
        """
        Test json response we get for user 10.
        """
        expected_data = utils.group_mean_start_end_by_weekday(utils.get_data()[10])
        for _, value in expected_data.items():
            value['start'] = value['start'].strftime('%H:%M:%S')
            value['end'] = value['end'].strftime('%H:%M:%S')

        response = self.client.get('/api/v1/presence_start_end/10')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_data, data)

    def test_start_end_weekday_view_for_non_existent_user(self):
        """
        Check response for user with id 1 not mentioned in test_data.csv is 404.
        """
        response = self.client.get('/api/v1/presence_start_end/1')

        self.assertEqual(response.status_code, 404)

    def test_mean_time_month_view(self):
        """
        Test JSON response for user 10.
        """
        expected_data = [
            ['Jan', [0, 0, 0]], ['Feb', [0, 0, 0]], ['Mar', [0, 0, 0]],
            ['Apr', [0, 0, 0]], ['May', [0, 0, 0]], ['Jun', [0, 0, 0]],
            ['Jul', [0, 0, 0]], ['Aug', [0, 0, 0]], ['Sep', [7, 14, 32]],
            ['Oct', [0, 0, 0]], ['Nov', [0, 0, 0]], ['Dec', [0, 0, 0]]
        ]

        response = self.client.get('/api/v1/mean_time_month/10')
        received_data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_data, received_data)

    def test_mean_time_month_for_non_existent_user(self):
        """
        Check response for user with id 1 not mentioned in test_data.csv is 404
        """
        response = self.client.get('/api/v1/mean_time_month/1')

        self.assertEqual(response.status_code, 404)

    def test_get_user_avatar_url(self):
        """
        Check url given for user 10.
        """
        response = self.client.get('/api/v1/user_avatar_url/10')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, '/api/images/users/10')

    def test_get_user_avatar_url_for_non_existent_user(self):
        """
        Request for non-existent user with ID 1 should return 404 code.
        """
        response = self.client.get('/api/v1/user_avatar_url/1')
        self.assertEqual(response.status_code, 404)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        utils._storage = {}

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
        self.assertItemsEqual(data.keys(), [10, 11, 13, 130])
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

    def test_seconds_to_time(self):
        """
        Tests seconds_to_time returns correct time.
        """
        self.assertEqual(utils.convert_seconds_to_time(0), datetime.time(0, 0, 0))
        self.assertEqual(utils.convert_seconds_to_time(1), datetime.time(0, 0, 1))
        self.assertEqual(utils.convert_seconds_to_time(70), datetime.time(0, 1, 10))
        self.assertEqual(utils.convert_seconds_to_time(7210), datetime.time(2, 0, 10))

    def test_group_start_end_by_weekday(self):
        """
        Test if group by weekday returns expected averages.
        """
        test_data = {
            datetime.date(2017, 4, 3): {
                'start': datetime.time(7, 0, 0),
                'end': datetime.time(17, 0, 0)
            },

            datetime.date(2017, 4, 10): {
                'start': datetime.time(7, 30, 0),
                'end': datetime.time(17, 30, 0)
            },

            datetime.date(2017, 4, 17): {
                'start': datetime.time(8, 00, 0),
                'end': datetime.time(18, 00, 0)
            }
        }
        expected_data = {
            day: {
                'start': datetime.time(0, 0, 0),
                'end': datetime.time(0, 0, 0)
            }
            for day in calendar.day_abbr
        }
        expected_data['Mon']['start'] = datetime.time(7, 30, 0)
        expected_data['Mon']['end'] = datetime.time(17, 30, 0)

        data = utils.group_mean_start_end_by_weekday(test_data)

        self.assertEqual(data, expected_data)

    def test_group_intervals_by_month(self):
        """
        Test if group by month returns expected averages. Test data average time is one hour.
        """
        test_data = {
            datetime.date(2017, 1, 3): {
                'start': datetime.time(6, 0, 0),
                'end': datetime.time(7, 30, 0)
            },
            datetime.date(2017, 1, 4): {
                'start': datetime.time(7, 0, 0),
                'end': datetime.time(7, 30, 0)
            }
        }
        expected_result = [[] for _ in range(12)]
        expected_result[0] = [1800, 5400]

        result = utils.group_intervals_by_month(test_data)

        self.assertEqual(result, expected_result)

    def test_get_user_data(self):
        """
        Test get_user_data_method() extracts users from test_users.xml file.
        """
        expected_result = {
            10: {
                'avatar_url': '/api/images/users/10',
                'name': 'Maciej Z.'
            },
            12: {
                'avatar_url': '/api/images/users/12',
                'name': 'Patryk G.'
            },
            11: {
                'avatar_url': '/api/images/users/11',
                'name': 'Maciej D.'
            }
        }
        result = utils.get_user_data()

        self.assertEqual(expected_result, result)

    def test_caching(self):
        """
        After calling get_data data should appear in cache.
        """
        self.assertEqual(utils._storage, {})
        result = utils.get_data()
        key = utils.get_key_hash(utils.get_data.__name__)
        self.assertEqual(result, utils._storage[key]['result'])


# We assume urllib is working fine, so we only mock the response in every call.
class PresenceAnalyzerCronJobTestCase(unittest.TestCase):
    """
    Test buildout crontabs.
    """
    def setUp(self):
        with open(TEST_USERS_XML_FILE) as user_file:
            self.user_file_contents = user_file.read()
        self.mocked_urllib_read = Mock(
            read=Mock(return_value=self.user_file_contents)
        )

    @patch('presence_analyzer.cronjobs.download_xml.os')
    @patch('presence_analyzer.cronjobs.download_xml.logger')
    @patch('presence_analyzer.cronjobs.download_xml.urllib.urlopen')
    def test_finds_existing_downloads(self, mocked_urlopen, mocked_logger, mocked_os):
        """
        download_xml() function should detect existing user xml files and log info about it.
        """
        mocked_urlopen.return_value = self.mocked_urllib_read
        download_xml.run_debug()

        self.assertEqual(mocked_logger.info.call_count, 1)
        self.assertEqual(mocked_logger.info.call_args[0], ('Found existing data file. Removing.',))
        mocked_os.remove.assert_called_with(os.path.normpath(TEST_USERS_XML_FILE))

    @patch('presence_analyzer.cronjobs.download_xml.os')
    @patch('presence_analyzer.cronjobs.download_xml.logger')
    @patch('presence_analyzer.cronjobs.download_xml.urllib.urlopen')
    def test_data_gets_saved(self, mocked_urlopen, mocked_logger, mocked_os):
        """
        Mocked data is "downloaded" from MockUrlLib, which returns the same contents as stored
        in test_users.xml. After download data should be stored in USERS_XML_FILE.
        """
        mocked_urlopen.return_value = self.mocked_urllib_read

        download_xml.run_debug()

        self.assertTrue(os.path.exists(main.app.config['USERS_XML_FILE']))
        self.assertEqual(self.user_file_contents, self.user_file_contents)


def suite():  # pragma: no cover
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerCronJobTestCase))
    return base_suite


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
