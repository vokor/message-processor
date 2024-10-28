import json
import pandas as pd
from abc import ABC, abstractmethod

from data_extractor import TelegramMessageProcessor
from utils import get_hash

DEFAULT_VALUE = 'nan'

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
            self.message_processor = self.start_process_chat(chat)
            for message in chat:
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
        self.process_chats(data['chats']['list'])

    def start_process_chat(self, chat):
        self.chat_info = {
            'chat_id': chat['id'],
            'partner_user_nickname': chat.get('name', DEFAULT_VALUE),
            'partner_used_id': get_hash(chat['name']) if 'name' in chat else DEFAULT_VALUE,
        }
        return TelegramMessageProcessor()

    def finish_process_chat(self):
        messages =  self.message_processor.data
        data = {key: [value] * len(next(iter(messages.values()))) for key, value in self.chat_info.items()}
        data.update(messages)
        return pd.DataFrame(data)

