import re
import json

import emoji
import pandas as pd

from data_extractor import MessageProcessor
from processors import Processor
from utils import MessageType, DEFAULT_VALUE, Platform, DEFAULT_VALUE_NUM


class TelegramMessageProcessor(MessageProcessor):
    def __init__(self, user_id_mapper):
        super().__init__(user_id_mapper)
        self.prev_date_unixtime = 0

    def get_timestamp(self):
        return int(self.message['date_unixtime'])

    def get_message_type(self):
        if self.message.get('media_type', '') == 'voice_message':
            return MessageType.MESSAGE_VOICE
        elif self.message.get('media_type', '') == 'video_message':
            return MessageType.MESSAGE_VIDEO
        elif self.message.get('action', '') == 'phone_call':
            return MessageType.CALL_AUDIO
        else:
            return MessageType.MESSAGE

    def get_symbols_count(self):
        return self.message_structure['symbols_count']

    def get_picture_count(self):
        return 1 if len(self.message.get('photo', '')) > 0 else 0

    def get_emoji_count(self):
        return self.message_structure['emoji_count']

    def get_link_count(self):
        return self.message_structure['links_count']

    def get_seconds_count(self):
        return self.message.get('duration_seconds', 0)

    def get_video_count(self):
        return 1 if self.message.get('media_type', '') == 'video_file' else 0

    def count_aggregates(self):
        def count_links(text):
            url_pattern = r'(https?://(?:www\.)?[^\s]+)'
            links = re.findall(url_pattern, text)
            return len(links)

        def count_symbols(text):
            return len(text)

        def count_emoji(text):
            emoji_list = [char for char in text if char in emoji.EMOJI_DATA]
            return len(emoji_list)

        message_text = self.message['text']
        if isinstance(message_text, str):
            return {
                "symbols_count": count_symbols(message_text),
                "links_count": count_links(message_text),
                "emoji_count": count_emoji(message_text) + count_emoji(self.message.get('sticker_emoji', ''))
            }
        elif isinstance(message_text, list):
            symbols_count = 0
            links_count = 0
            emoji_count = 0
            for item in message_text:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    symbols_count += count_symbols(text)
                    links_count += count_links(text) + count_links(item.get("href", ""))
                    emoji_count += count_emoji(text)
                else:
                    symbols_count += count_symbols(item)
                    links_count += count_links(item)
                    emoji_count += count_emoji(item)
            return {
                "symbols_count": symbols_count,
                "links_count": links_count,
                "emoji_count": emoji_count
            }
        else:
            raise Exception("failed to parse message:" + str(self.message))

    def update_aggregated_chat_info(self):
        self.message_structure = self.count_aggregates()
        if self.get_timestamp() == self.prev_date_unixtime and self.get_message_type() == self.data['message_type'][-1]:
            self.need_append_message = False
            self.data['picture_count'][-1] += self.get_picture_count()
            self.data['video_count'][-1] += self.get_video_count()
            self.data['seconds_count'][-1] += self.get_seconds_count()
        else:
            self.need_append_message = True
            self.prev_date_unixtime = self.get_timestamp()

    def get_target_used_id(self):
        for value in self.user_id_mapper.values():
            return value

    def get_active_user_id(self):
        from_id = int(self.get_or_else('from_id', 'actor_id')[4:])
        return self.user_id_mapper.get(from_id, from_id)

    def get_active_user_nickname(self):
        return self.get_or_else('from', 'actor')

    def start(self):
        return

    def need_process_message(self):
        return self.message['type'] == 'message' or self.get_message_type() == MessageType.CALL_AUDIO

    def get_is_forwarded(self):
        return self.message.get('forwarded_from', DEFAULT_VALUE) != DEFAULT_VALUE

    def parse(self):
        parsed_json = json.loads(self.data)
        print(len(parsed_json['chats']))


class TelegramProcessor(Processor):
    def __init__(self, data, custom_target_user_id):
        super().__init__(Platform.TELEGRAM, custom_target_user_id)
        self.data = data

    def parse(self):
        parsed_json = json.loads(self.data)
        return parsed_json

    def run(self):
        data = self.parse()
        personal_info = data['personal_information']
        self.context.update({
            'target_used_id': personal_info['user_id'],
            'nickname': personal_info['first_name'] + ' ' + personal_info['last_name']
        })
        self.user_id_mapper = {personal_info['user_id']: self.custom_target_user_id}
        self.process_chats(data['chats']['list'])

    def start_process_chat(self, chat, user_id_mapper):
        self.chat_info = {
            'chat_id': chat['id'],
            'chat_users_count': 2 if chat.get('type', DEFAULT_VALUE) == 'personal_chat' else -1,
        }
        if self.chat_info['chat_users_count'] == 2:
            self.chat_info['partner_used_id'] = chat['id']
            self.chat_info['partner_user_nickname'] = chat['name']
        else:
            self.chat_info['partner_used_id'] = DEFAULT_VALUE_NUM
            self.chat_info['partner_user_nickname'] = DEFAULT_VALUE
        return TelegramMessageProcessor(user_id_mapper)

    def finish_process_chat(self):
        messages = self.message_processor.data
        if len(messages) == 0:
            return pd.DataFrame()
        if self.chat_info['chat_users_count'] == -1:
            self.chat_info['chat_users_count'] = len(set(messages['active_user_id']))
        data = {key: [value] * len(next(iter(messages.values()))) for key, value in self.chat_info.items()}
        data.update(messages)
        return pd.DataFrame(data)