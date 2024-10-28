import re
import json

import emoji
from abc import ABC, abstractmethod
from collections import defaultdict


class Platform:
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    VK = "vk"

class MessageType:
    MESSAGE = "0"
    MESSAGE_VIDEO = "1"
    CALL_VOICE = "2"
    CALL_VIDEO = "3"
    CALL_UNDEFINED = "4"

PLATFORM_TO_ID = {
    Platform.TELEGRAM: 1,
    Platform.WHATSAPP: 2,
    Platform.VK: 3,
}

class MessageProcessor(ABC):
    def __init__(self):
        self.context = {}
        self.data = defaultdict(list)

    def process(self, message):
        self.update_aggregated_chat_info(message)
        self.message = message
        self.data['partner_user_nickname'].append(self.get_partner_user_nickname())
        self.data['partner_used_id'].append(self.get_partner_used_id())
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
    def update_aggregated_chat_info(self, message):
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
    def get_partner_used_id(self):
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


class TelegramMessageProcessor(MessageProcessor):
    def get_timestamp(self):
        return self.message['date_unixtime']

    def get_message_type(self):
        if len(self.message.get('text', '')) > 0:
            return MessageType.MESSAGE
        elif self.message.get('media_file', '') == 'video_file':
            return MessageType.MESSAGE_VIDEO
        else:
            raise Exception(str(self.message))

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
        pass

    def get_video_count(self):
        pass

    def update_aggregated_chat_info(self, message):
        pass

    def process(self, message):
        pass

    def get_target_used_id(self):
        pass

    def get_partner_user_nickname(self):
        pass

    def get_partner_used_id(self):
        pass

    def start(self):
        return

    def parse(self):
        parsed_json = json.loads(self.data)
        print(len(parsed_json['chats']))