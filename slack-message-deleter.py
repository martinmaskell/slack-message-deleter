#!/usr/bin/env python3
import requests
import time
import urllib.parse

WORKSPACE = '<< insert your workspace here. e.g. mycompanydevteam.slack.com >>'

# Get this from Form Data
TOKEN = '<< insert token string here. e.g. xoxc-123456789012-123456789012-123456789012-f123jj5186rr78f395aecf2ccff281h1234b456789123f45678c4c7984e65a5k >>'

# Get this from Request Headers
COOKIE = '<< insert cookie string here >>'

# Inspect your username element, you'll see it at the end of the href
USER = '<< insert user string here. e.g. ABCDE1FG2 >> '

# This is in the URL when you click on a Channel or DM
CHANNEL = '<< insert channel string here. e.g. AAAA6B7CD >>'
RATE_LIMIT_DELAY_MILLISECONDS = 4000


def get_request_headers():
    return {
        'authority': WORKSPACE,
        'cookie': COOKIE,
        'origin': 'https://app.slack.com'
    }


def build_base_form_data():
    return {
        'token': TOKEN,
    }


def send_request(method, cursor, params):
    form_data = build_base_form_data()

    if cursor is not None:
        form_data['cursor'] = cursor

    query = urllib.parse.urlencode(params)

    try:
        response = requests.post(
            f'https://{WORKSPACE}/api/{method}?{query}',
            headers=get_request_headers(),
            data=form_data
        )
    except Exception as e:
        return {'ok': False, 'exception': e}

    return response.json()


def get_conversations_history(cursor, channel):
    return send_request('conversations.history', cursor, {'channel': channel, 'limit': 200})


def get_conversations_list(cursor):
    return send_request('conversations.list', cursor, {'types': 'public_channel,private_channel,mpim,im', 'limit': 100})


def get_users(cursor):
    return send_request('users.list', cursor, {'limit': 20})


def get_all_users():
    cursor = None
    more = True

    users = {}

    while more:
        r = get_users(cursor)
        if not r['ok']:
            return users

        if 'next_cursor' in r['response_metadata'] and len(r['response_metadata']['next_cursor']) > 0:
            cursor = r['response_metadata']['next_cursor']
        else:
            more = False
            cursor = None

        for user in r['members']:
            users[user['id']] = user['name']

    return users


def get_user_messages(user, channel):
    cursor = None
    more_messages = True

    user_messages = []

    while more_messages:
        r = get_conversations_history(cursor, channel)
        if not r['ok']:
            return user_messages

        if 'has_more' in r and r['has_more']:
            cursor = r['response_metadata']['next_cursor']
        else:
            more_messages = False
            cursor = None

        for message in r['messages']:
            if 'user' in message and message['user'] == user:
                user_messages.append(message)

    return user_messages


def get_channels():
    cursor = None
    more_channels = True

    active_channels = []

    while more_channels:
        r = get_conversations_list(cursor)
        if 'ok' not in r or not r['ok']:
            return active_channels

        if 'has_more' in r and r['has_more']:
            cursor = r['response_metadata']['next_cursor']
        else:
            more_channels = False
            cursor = None

        for channel in r['channels']:
            is_member_of_channel = 'is_member' in channel and channel['is_member']
            is_group = 'is_group' in channel and channel['is_group']
            is_dm = 'is_im' in channel and channel['is_im'] and not channel['is_user_deleted']

            if is_member_of_channel or is_group or is_dm:
                active_channels.append(channel)

    return active_channels


def delete_message(message_timestamp, channel):
    while True:
        response = requests.post(
            f'https://{WORKSPACE}/api/chat.delete',
            headers=get_request_headers(),
            data={
                'channel': channel,
                'ts': message_timestamp,
                'token': TOKEN
            }
        )
        r = response.json()
        if not r['ok'] and r['error'] == 'ratelimited':
            time.sleep(RATE_LIMIT_DELAY_MILLISECONDS)
        else:
            break


if __name__ == "__main__":

    users = get_all_users()
    channels = get_channels()

    print(f'Delete all your messages from {len(channels)} channels, groups and DMs (Y/N)? ', end='')
    answer = input()

    if answer.lower() != 'y':
        exit()

    print('')
    for c in channels:

        if 'name' in c:
            name = c['name']
        else:
            name = users[c['user']]

        print(f"Deleting messages from {c['id']} {name}", end='')
        messages = get_user_messages(USER, c['id'])

        for m in messages:
            delete_message(m["ts"], c['id'])
            print('.', end='')

        print('\r')

    print("DONE!")
