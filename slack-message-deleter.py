#!/usr/bin/env python3
import requests
import time
import urllib.parse
import sys

WORKSPACE = '<< insert your workspace here. e.g. mycompanydevteam.slack.com >>'

# Get this from Form Data
TOKEN = '<< insert token string here. e.g. xoxc-123456789012-123456789012-123456789012-f123jj5186rr78f395aecf2ccff281h1234b456789123f45678c4c7984e65a5k >>'

# Get this from Request Headers
COOKIE = '<< insert cookie string here >>'

# Inspect your username element, you'll see it at the end of the href
USER = '<< insert user string here. e.g. ABCDE1FG2 >> '


class SlackMessageDeleter:

    DEFAULT_DELETE_DELAY_IN_SECONDS = 0.2

    def __init__(self, workspace, token, cookie, user):
        self.__workspace = workspace
        self.__token = token
        self.__cookie = cookie
        self.__user = user
        self.__message_delete_delay_in_seconds = self.DEFAULT_DELETE_DELAY_IN_SECONDS
        self.__delay_delete_request_enabled = False

    def __get_request_headers(self):
        return {
            'authority': self.__workspace,
            'cookie': self.__cookie,
            'origin': 'https://app.slack.com'
        }

    def __build_base_form_data(self):
        return {
            'token': self.__token,
        }

    def __send_request(self, method, cursor, params):
        form_data = self.__build_base_form_data()

        if cursor is not None:
            form_data['cursor'] = cursor

        query = urllib.parse.urlencode(params)

        try:
            response = requests.post(
                f'https://{self.__workspace}/api/{method}?{query}',
                headers=self.__get_request_headers(),
                data=form_data
            )
        except Exception as e:
            return {'ok': False, 'exception': e}

        return response.json()

    def __get_conversations_history(self, cursor, channel):
        return self.__send_request('conversations.history', cursor, {'channel': channel, 'limit': 200})

    def __get_conversations_list(self, cursor):
        return self.__send_request('conversations.list', cursor, {'types': 'public_channel,private_channel,mpim,im',
                                                                  'limit': 100})

    def __get_users(self, cursor):
        return self.__send_request('users.list', cursor, {'limit': 20})

    def __get_all_users(self):
        cursor = None
        more = True

        all_users = {}

        while more:
            users_response = self.__get_users(cursor)
            if not users_response['ok']:
                return all_users

            if 'next_cursor' in users_response['response_metadata'] and len(users_response['response_metadata']['next_cursor']) > 0:
                cursor = users_response['response_metadata']['next_cursor']
            else:
                more = False
                cursor = None

            for user in users_response['members']:
                all_users[user['id']] = user['name']

        return all_users

    def __get_user_messages(self, user, channel):
        cursor = None
        more_messages = True

        user_messages = []

        while more_messages:
            conversation_dictionary = self.__get_conversations_history(cursor, channel)
            if not conversation_dictionary['ok']:
                return user_messages

            if 'has_more' in conversation_dictionary and conversation_dictionary['has_more']:
                cursor = conversation_dictionary['response_metadata']['next_cursor']
            else:
                more_messages = False
                cursor = None

            for message in conversation_dictionary['messages']:
                if 'user' in message and message['user'] == user:
                    user_messages.append(message)

        return user_messages

    def __get_channels(self):
        cursor = None
        more_channels = True

        active_channels = []

        while more_channels:
            conversations_dictionary = self.__get_conversations_list(cursor)
            if 'ok' not in conversations_dictionary or not conversations_dictionary['ok']:
                return active_channels

            if 'has_more' in conversations_dictionary and conversations_dictionary['has_more']:
                cursor = conversations_dictionary['response_metadata']['next_cursor']
            else:
                more_channels = False
                cursor = None

            for channel in conversations_dictionary['channels']:
                is_member_of_channel = 'is_member' in channel and channel['is_member']
                is_group = 'is_group' in channel and channel['is_group']
                is_dm = 'is_im' in channel and channel['is_im'] and not channel['is_user_deleted']

                if is_member_of_channel or is_group or is_dm:
                    active_channels.append(channel)

        return active_channels

    def __delete_message(self, message_timestamp, channel):

        while True:
            if self.__delay_delete_request_enabled:
                time.sleep(self.__message_delete_delay_in_seconds)

            response = requests.post(
                f'https://{self.__workspace}/api/chat.delete',
                headers=self.__get_request_headers(),
                data={
                    'channel': channel,
                    'ts': message_timestamp,
                    'token': self.__token
                }
            )
            response_dictionary = response.json()

            if not response_dictionary['ok'] and response_dictionary['error'] == 'ratelimited':
                if self.__delay_delete_request_enabled:
                    self.__message_delete_delay_in_seconds = self.__message_delete_delay_in_seconds + 0.1
                else:
                    self.__delay_delete_request_enabled = True
            else:
                break

    def delete_all_messages(self):

        users = self.__get_all_users()
        channels = self.__get_channels()

        print(f'Delete all your messages from {len(channels)} channels, groups and DMs (Y/N)? ', end='')
        user_prompt_answer = input()
        if user_prompt_answer.lower() != 'y':
            exit()

        print('')
        for channel in channels:
            if 'name' in channel:
                name = channel['name']
            else:
                name = users[channel['user']]

            print(f"Deleting messages from {channel['id']} {name}", end='')
            messages = self.__get_user_messages(self.__user, channel['id'])

            if len(messages) > 0:
                print(f' ({len(messages):,} messages)...', end='')

            deleted_counter = 0

            for message in messages:
                self.__delete_message(message["ts"], channel['id'])

                if deleted_counter > 0:
                    leng = len(str(deleted_counter))
                    for i in range(leng):
                        sys.stdout.write('\b')

                deleted_counter = deleted_counter + 1
                sys.stdout.write(str(deleted_counter))

            print('\r')

        print("DONE!")


if __name__ == "__main__":

    deleter = SlackMessageDeleter(WORKSPACE, TOKEN, COOKIE, USER)
    deleter.delete_all_messages()

