import pandas as pd
from abc import ABC, abstractmethod

class Processor(ABC):
    def __init__(self, name, custom_target_user_id):
        self.custom_target_user_id = custom_target_user_id
        self.context = {
            'name': name
        }
        self.processed = pd.DataFrame()

    @abstractmethod
    def run(self):
        pass

    def process_chats(self, chats):
        for chat in chats:
            self.message_processor = self.start_process_chat(chat, self.user_id_mapper)
            for message in chat['messages']:
                self.message_processor.process(message)
            self.processed = pd.concat([self.finish_process_chat(), self.processed], ignore_index=True)

    @abstractmethod
    def start_process_chat(self, chat, user_id_mapper):
        pass

    @abstractmethod
    def finish_process_chat(self):
        pass



