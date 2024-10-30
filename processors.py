import json
import pandas as pd
from abc import ABC, abstractmethod

from data_extractor import TelegramMessageProcessor
from utils import Platform, DEFAULT_VALUE, DEFAULT_VALUE_NUM

class Processor(ABC):
    def __init__(self, name, custom_target_user_id):
        self.custom_target_user_id = custom_target_user_id
        self.context = {
            'name': name
        }

    @abstractmethod
    def parse(self):
        pass

    @abstractmethod
    def run(self):
        pass

    def process_chats(self, chats):
        for chat in chats:
            self.message_processor = self.start_process_chat(chat, self.user_id_mapper)
            for message in chat['messages']:
                self.message_processor.process(message)
            self.finish_process_chat()

    @abstractmethod
    def start_process_chat(self, chat):
        pass

    @abstractmethod
    def finish_process_chat(self):
        pass


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
        self.chat_info['partner_used_id'] = chat['id'] if self.chat_info['chat_users_count'] == 2 else DEFAULT_VALUE_NUM
        return TelegramMessageProcessor(user_id_mapper)

    def finish_process_chat(self):
        messages = self.message_processor.data
        if self.chat_info['chat_users_count'] == -1:
            self.chat_info['chat_users_count'] = len(set(messages['active_user_id']))
        data = {key: [value] * len(next(iter(messages.values()))) for key, value in self.chat_info.items()}
        data.update(messages)
        return pd.DataFrame(data)
