# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar

from flask import redirect, abort
from flask.helpers import url_for
from flask_mako import render_template

from .main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    mean,
    group_by_weekday,
    group_mean_start_end_by_weekday,
    get_user_data
)

import logging
log = logging.getLogger(__name__)  # pylint: disable=invalid-name

templates = {
    'mean_time_weekday': {
        'name': 'mean_time_weekday',
        'description': 'Presence mean time',
        'template': 'mean_time_weekday.html'
    },
    'presence_weekday': {
        'name': 'presence_weekday',
        'description': 'Presence by weekday',
        'template': 'presence_weekday.html'
    },
    'presence_start_end': {
        'name': 'presence_start_end',
        'description': 'Presence start-end',
        'template': 'presence_start_end.html'
    }
}


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect(url_for('statistics_view', chosen='presence_weekday'))


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown consisting of user_id, name and image url. If user data can be found
    in USERS_XML_FILE, user's actual name is used and image_url is added. Otherwise, id is used and
    avatar_url is set to null.
    """
    data = get_data()
    users_data = get_user_data()

    result = []

    for i in data.keys():
        try:
            result.append({
                'user_id': i,
                'name': users_data[i]['name'],
            })
        except KeyError:
            result.append({
                'user_id': i,
                'name': 'User {}'.format(str(i)),
            })
    return result


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_api_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_api_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_api_view(user_id):
    """
    Return json response for mean time user with given id has come to and from work.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found', user_id)
        abort(404)

    weekdays = group_mean_start_end_by_weekday(data[user_id])

    for day, value in weekdays.items():
        value['start'] = value['start'].strftime('%H:%M:%S')
        value['end'] = value['end'].strftime('%H:%M:%S')

    return weekdays


@app.route('/api/v1/user_avatar_url/<user_id>', methods=['GET'])
@jsonify
def get_user_avatar_url(user_id):
    """
    Fetches avatar url from USERS_XML_FILE for given user. 404 if its not found.
    """
    user_data = get_user_data()
    try:
        return user_data[int(user_id)]['avatar_url']
    except KeyError:
        abort(404)


@app.route('/statistics/<chosen>/')
def statistics_view(chosen):
    try:
        return render_template(templates[chosen]['template'], templates=templates)
    except KeyError:
        abort(404)
