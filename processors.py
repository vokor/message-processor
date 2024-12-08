import pandas as pd
from abc import ABC, abstractmethod

class Processor(ABC):
    def __init__(self, name, custom_target_user_id, update_progress):
        self.custom_target_user_id = custom_target_user_id
        self.context = {
            'name': name
        }
        self.update_progress = update_progress
        self.processed = pd.DataFrame()
        self.skipped_chats = 0
        self.all_chats = 0
        self.skipped_chat_ids = []


    @abstractmethod
    def run(self):
        pass

    def process_chats(self, chats):
        chats_len = float(len(chats))
        self.all_chats = int(chats_len)
        processed_num = 0
        for chat in chats:
            self.message_processor = self.start_process_chat(chat, self.user_id_mapper)
            for message in chat['messages']:
                if not self.message_processor.continue_processing:
                    break
                self.message_processor.time = None
                self.message_processor.process(message)
            if self.message_processor.continue_processing:
                self.processed = pd.concat([self.finish_process_chat(), self.processed], ignore_index=True)
            else:
                self.skipped_chats += 1
                self.skipped_chat_ids.append(self.chat_info['chat_id'])
            processed_num += 1
            self.update_progress(100 * processed_num / chats_len)
            chat.clear()

    @abstractmethod
    def start_process_chat(self, chat, user_id_mapper):
        pass

    @abstractmethod
    def finish_process_chat(self):
        pass



