# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""
from __future__ import unicode_literals

import calendar
import csv
import logging
import datetime
from json import dumps
from functools import wraps
from lxml import etree

from flask import Response

from presence_analyzer.main import app

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=str(','))
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def group_mean_start_end_by_weekday(items):
    """
    Groups start and end time by weekdays. Returns a list with consecutive statistics for each
    weekday in a form of:
        [ [day of the week, mean start time, mean end time], ... ]
    The start end end times are returned as datetime.time() objects.
    """

    presence_list = {
        day: {
            'start': [],
            'end': []
        }
        for day in calendar.day_abbr
    }

    for date in items:
        start = seconds_since_midnight(items[date]['start'])
        end = seconds_since_midnight(items[date]['end'])
        weekday_name = calendar.day_abbr[date.weekday()]

        presence_list[weekday_name]['start'].append(start)
        presence_list[weekday_name]['end'].append(end)

    for day, values in presence_list.items():
        values['start'] = convert_seconds_to_time(int(mean(values['start'])))
        values['end'] = convert_seconds_to_time(int(mean(values['end'])))

    return presence_list


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def convert_seconds_to_time(seconds):
    """
    Calculate time of the day based on seconds since midnight.
    """
    hour = seconds // 3600
    seconds %= 3600
    minute = seconds // 60
    seconds %= 60
    return datetime.time(hour=hour, minute=minute, second=seconds)


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def get_user_data():
    """
    Extracts user data from .tree files. Returns dictionary in following format:
        {
            <id>: {
                'name': <name>
                'avatar': <avatar_url>
            },
        }
    """
    result = {}

    tree = etree.parse(app.config['USERS_XML_FILE'])
    user_ids = tree.xpath('/intranet/users/user')
    user_names = tree.xpath('/intranet/users/user/name/text()')
    user_avatars = tree.xpath('/intranet/users/user/avatar/text()')

    for uid, name, avatar in zip(user_ids, user_names, user_avatars):
        result[int(uid.attrib['id'])] = {
            'name': name,
            'avatar_url': avatar
        }

    return result
