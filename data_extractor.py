import re
import json

import emoji
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from collections import defaultdict

from utils import PLATFORM_TO_ID, MessageType, DEFAULT_VALUE


class MessageProcessor(ABC):
    def __init__(self, user_id_mapper):
        self.context = {}
        self.data = defaultdict(list)
        self.need_append_message = True
        self.time_border = int((datetime.now() - timedelta(days=5 * 365)).timestamp())
        self.user_id_mapper = user_id_mapper

    def process(self, message):
        self.message = message
        if not self.need_process_message() or self.time_border > self.get_timestamp():
            return
        self.update_aggregated_chat_info()
        if self.need_append_message:
            self.data['partner_user_nickname'].append(self.get_partner_user_nickname())
            self.data['partner_used_id'].append(self.get_partner_user_id())
            self.data['active_user_id'].append(self.get_partner_user_nickname())
            self.data['timestamp'].append(self.get_timestamp())
            self.data['message_type'].append(self.get_message_type())
            self.data['symbols_count'].append(self.get_symbols_count())
            self.data['picture_count'].append(self.get_picture_count())
            self.data['emoji_count'].append(self.get_emoji_count())
            self.data['link_count'].append(self.get_link_count())
            self.data['video_count'].append(self.get_video_count())
            self.data['seconds_count'].append(self.get_seconds_count())

    @abstractmethod
    def update_aggregated_chat_info(self):
        pass

    def get_aggregated_chat_info(self):
        return {
            'messenger_type': PLATFORM_TO_ID[self.context.name],
            'target_user_id': self.get_target_used_id(),
            'chat_id': self.context.chat_id,
            'chat_users_count': self.context.chat_users_count
        }

    @abstractmethod
    def get_target_used_id(self):
        pass

    @abstractmethod
    def get_partner_user_nickname(self):
        pass

    @abstractmethod
    def get_partner_user_id(self):
        pass

    @abstractmethod
    def get_timestamp(self):
        pass

    @abstractmethod
    def get_message_type(self):
        pass

    @abstractmethod
    def get_symbols_count(self):
        pass

    @abstractmethod
    def get_picture_count(self):
        pass

    @abstractmethod
    def get_emoji_count(self):
        pass

    @abstractmethod
    def get_link_count(self):
        pass

    @abstractmethod
    def get_video_count(self):
        pass

    @abstractmethod
    def get_seconds_count(self):
        pass

    @abstractmethod
    def need_process_message(self):
        return True


class TelegramMessageProcessor(MessageProcessor):
    def __init__(self, user_id_mapper):
        super().__init__(user_id_mapper)
        self.prev_date_unixtime = 0

    def get_timestamp(self):
        return int(self.message['date_unixtime'])

    def get_message_type(self):
        if self.message.get('media_type', '') == 'voice_message':
            return MessageType.CALL_VOICE
        elif self.message.get('media_type', '') == 'video_message':
            return MessageType.MESSAGE_VIDEO
        else:
            return MessageType.MESSAGE

    def get_symbols_count(self):
        return len(self.message.get('text', ''))

    def get_picture_count(self):
        return 1 if len(self.message.get('photo', '')) > 0 else 0

    def get_emoji_count(self):
        emoji_list = [char for char in self.message.get('text', '') if char in emoji.EMOJI_DATA]
        return len(emoji_list)

    def get_link_count(self):
        url_pattern = r'(https?://(?:www\.)?[^\s]+)'
        links = re.findall(url_pattern, self.message.get('text', ''))
        return len(links)

    def get_seconds_count(self):
        return self.message.get('duration_seconds', 0)

    def get_video_count(self):
        return 1 if self.message.get('media_file', '') == 'video_file' else 0

    def update_aggregated_chat_info(self):
        if self.message["date_unixtime"] == self.prev_date_unixtime and self.get_message_type() == \
                self.data['message_type'][-1]:
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

    def get_partner_user_id(self):
        from_id = int(self.message['from_id'][4:])
        return self.user_id_mapper.get(from_id, from_id)

    def get_partner_user_nickname(self):
        return self.message['from']

    def start(self):
        return

    def need_process_message(self):
        return self.message['type'] == 'message' and self.message.get('forwarded_from', DEFAULT_VALUE) == DEFAULT_VALUE

    def parse(self):
        parsed_json = json.loads(self.data)
        print(len(parsed_json['chats']))
