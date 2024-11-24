from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from collections import defaultdict

from utils import PLATFORM_TO_ID


class MessageProcessor(ABC):
    def __init__(self, user_id_mapper):
        self.context = {}
        self.data = defaultdict(list)
        self.need_append_message = True
        self.time_border = int((datetime.now() - timedelta(days=5 * 365)).timestamp())
        self.user_id_mapper = user_id_mapper

    def get_or_else(self, one, another):
        if one in self.message:
            return self.message.get(one)
        else:
            return self.message.get(another)

    def process(self, message):
        self.message = message
        if self.get_timestamp() == 1728634725:
            a = 1
        if not self.need_process_message() or self.time_border > self.get_timestamp():
            return
        self.update_aggregated_chat_info()
        if self.need_append_message:
            self.data['active_user_nickname'].append(self.get_active_user_nickname())
            self.data['active_user_id'].append(self.get_active_user_id())
            self.data['timestamp'].append(self.get_timestamp())
            self.data['message_type'].append(self.get_message_type())
            self.data['symbols_count'].append(self.get_symbols_count())
            self.data['picture_count'].append(self.get_picture_count())
            self.data['emoji_count'].append(self.get_emoji_count())
            self.data['link_count'].append(self.get_link_count())
            self.data['video_count'].append(self.get_video_count())
            self.data['seconds_count'].append(self.get_seconds_count())
            self.data['is_forwarded'].append(self.get_is_forwarded())

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
    def get_active_user_nickname(self):
        pass

    @abstractmethod
    def get_active_user_id(self):
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

    @abstractmethod
    def get_is_forwarded(self):
        return False
