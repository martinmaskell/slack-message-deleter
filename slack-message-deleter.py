import os
import requests
import time
import urllib.parse
import sys
import shutil

WORKSPACE = '<< mycompanydevteam.slack.com >>'

# Get this from Form Data
TOKEN = '<< xoxc-123456789012-123456789012-123456789012-f123jj5186rr78f395aecf2ccff281h1234b456789123f45678c4c7984e65a5k >>'

# Get this from Request Headers
COOKIE = '<< insert cookie string here >>'

# Inspect your username element, you'll see it at the end of the href
USER = '<< ABCDE1FG2 >> '


class SlackMessageDeleter:

    DEFAULT_DELETE_DELAY_IN_SECONDS = 0.2
    FILE_SAVE_FOLDER = 'downloads'

    def __init__(self, workspace, token, cookie, user):
        self.__workspace = workspace
        self.__token = token
        self.__cookie = cookie
        self.__user = user
        self.__message_delete_delay_in_seconds = self.DEFAULT_DELETE_DELAY_IN_SECONDS
        self.__delay_delete_request_enabled = False

        if not os.path.exists(self.FILE_SAVE_FOLDER):
            os.makedirs(self.FILE_SAVE_FOLDER)

    @staticmethod
    def __try_parse_int(string, base=10, val=None):
        try:
            return int(string, base)
        except ValueError:
            return val

    def __get_file_save_path(self, channel_id):
        path = self.FILE_SAVE_FOLDER + '/' + channel_id
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @staticmethod
    def __get_file_name_save_path(save_folder, file):
        file_name = file['name']
        local_file_path = save_folder + '/' + file_name

        if os.path.isfile(local_file_path):
            file_name_parts = file_name.split('.')
            name = '.'.join(file_name_parts[0:-1])
            ext = file_name_parts[-1]
            local_file_path = f"{save_folder}/{name}.{str(file['timestamp'])}.{ext}"

        return local_file_path

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

    def __get_messages(self, user, channel):
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
                if user is None or ('user' in message and message['user'] == user):
                    user_messages.append(message)

        return user_messages

    @staticmethod
    def __get_files_from_messages(messages):
        files = []
        for m in messages:
            if 'files' in m:
                for file in m['files']:
                    files.append(file)
        return files

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

        user_prompt_answer = input(f'Delete all your messages from {len(channels)} channels, groups and DMs (Y/N)? ')
        if user_prompt_answer.lower() != 'y':
            exit()

        print('')
        for channel in channels:
            if 'name' in channel:
                name = channel['name']
            else:
                name = users[channel['user']]

            print(f"Deleting messages from {channel['id']} {name}", end='')
            messages = self.__get_messages(self.__user, channel['id'])

            if len(messages) > 0:
                print(f' ({len(messages):,} messages)...', end='')

            for index, message in enumerate(messages, start=1):
                self.__delete_message(message["ts"], channel['id'])

                if index > 1:
                    index_string_length = len(str(index-1))
                    for i in range(index_string_length):
                        sys.stdout.write('\b')

                sys.stdout.write(str(index))

            print('\r')

        print("DONE!")

    @staticmethod
    def __display_channels(channels, users):
        for index, channel in enumerate(channels, start=1):
            if 'name' in channel:
                name = channel['name']
            else:
                name = users[channel['user']]

            print(f'{index}: {name}')

    def download_files(self):
        users = self.__get_all_users()
        channels = self.__get_channels()

        print('----------------')
        print('File Downloader')
        print('----------------')

        self.__display_channels(channels, users)

        selected_channel_index = self.__try_parse_int(
            input(r'Choose a channel from where to download the files: '), 0)
        if selected_channel_index < 1 or selected_channel_index > len(channels):
            exit()

        selected_channel = channels[selected_channel_index-1]
        channel_id = selected_channel['id']
        save_path = self.__get_file_save_path(channel_id)

        messages = self.__get_messages(None, channel_id)
        files = self.__get_files_from_messages(messages)

        continue_download_answer = input(f'Download {len(files)} files (Y/N)? ')
        if continue_download_answer.lower() == 'y':

            print(f'Downloading {len(files)} files...', end='')

            for index, file in enumerate(files, start=1):
                file_url = file['url_private_download']
                local_file_path = self.__get_file_name_save_path(save_path, file)

                file_response = requests.get(file_url, headers=self.__get_request_headers(), stream=True)
                if file_response.status_code == 200:
                    self.__save_file(file_response, local_file_path)

                    if index > 1:
                        index_string_length = len(str(index-1))
                        for i in range(index_string_length):
                            sys.stdout.write('\b')

                    sys.stdout.write(str(index))

        print("\rDONE!")

    @staticmethod
    def __save_file(file_response, local_file_path):
        local_file = open(local_file_path, 'wb')
        file_response.raw.decode_content = True
        shutil.copyfileobj(file_response.raw, local_file)

    def __files_search(self, channel_id):
        files = []
        page = 1
        total_pages = 0
        while True:
            response = self.__send_request('files.list', None, {'channel': channel_id, 'types': 'all', 'page': page})
            if 'ok' in response and response['ok']:
                if total_pages == 0:
                    total_pages = response['paging']['pages']

            for file in response['files']:
                files.append(file)

            if page == total_pages:
                break

            page += 1

        return files

    def __filter_file_by_user(self, file):
        return file['user'] == self.__user

    def __delete_files(self, files):
        print(f'Deleting {len(files)} files...', end='')
        for index, file in enumerate(files, start=1):
            if file['user'] == self.__user:
                self.__send_request('files.delete', None, {'file': file['id']})

                if index > 1:
                    index_string_length = len(str(index - 1))
                    for i in range(index_string_length):
                        sys.stdout.write('\b')

                sys.stdout.write(str(index))

    def download_files_from_search(self):

        users = self.__get_all_users()
        channels = self.__get_channels()

        print('----------------')
        print('File Downloader')
        print('----------------')

        self.__display_channels(channels, users)

        selected_channel_index = self.__try_parse_int(
            input(r'Choose a channel from where to download the files: '), 0)
        if selected_channel_index < 1 or selected_channel_index > len(channels):
            exit()

        selected_channel = channels[selected_channel_index - 1]
        channel_id = selected_channel['id']
        save_path = self.__get_file_save_path(channel_id)

        files = self.__files_search(channel_id)

        continue_download_answer = input(f'Download {len(files)} files (Y/N)? ')
        if continue_download_answer.lower() == 'y':

            print(f'Downloading {len(files)} files...', end='')

            for index, file in enumerate(files, start=1):
                file_url = file['url_private_download']
                local_file_path = self.__get_file_name_save_path(save_path, file)

                file_response = requests.get(file_url, headers=self.__get_request_headers(), stream=True)
                if file_response.status_code == 200:
                    self.__save_file(file_response, local_file_path)

                    if index > 1:
                        index_string_length = len(str(index - 1))
                        for i in range(index_string_length):
                            sys.stdout.write('\b')

                    sys.stdout.write(str(index))

        user_files = list(filter(self.__filter_file_by_user, files))

        delete_files_answer = input(f'\rDelete your {len(user_files)} files (Y/N)? ')
        if delete_files_answer.lower() == 'y':
            self.__delete_files(user_files)

        print("\rDONE!")


if __name__ == "__main__":

    slack = SlackMessageDeleter(WORKSPACE, TOKEN, COOKIE, USER)
    slack.delete_all_messages()
    slack.download_files_from_search()
