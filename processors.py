import json

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
        for chat_index, chat in enumerate(chats, start=1):
            self.message_processor = self.start_process_chat(chat)
            for message_index, message in enumerate(chat['messages'], start=1):
                if not self.message_processor.continue_processing:
                    break
                self.message_processor.time = None
                try:
                    self.message_processor.process(message)
                except Exception as exc:
                    # Report structure and location, never the message body.
                    record = message if isinstance(message, dict) else {}
                    rich_message = record.get('rich_message')
                    details = {
                        'platform': self.context.get('name'),
                        'chat_id': chat.get('id'),
                        'chat_index': chat_index,
                        'message_id': record.get('id'),
                        'message_index': message_index,
                        'message_object_type': type(message).__name__,
                        'type': record.get('type'),
                        'action': record.get('action'),
                        'media_type': record.get('media_type'),
                        'keys': sorted(record.keys()),
                        'text_present': 'text' in record,
                        'text_type': type(record['text']).__name__ if 'text' in record else None,
                        'rich_message_present': 'rich_message' in record,
                        'rich_message_type': type(rich_message).__name__ if 'rich_message' in record else None,
                        'rich_message_keys': sorted(rich_message.keys()) if isinstance(rich_message, dict) else None,
                    }
                    raise RuntimeError(
                        'Message processing failed; diagnostics: '
                        + json.dumps(details, ensure_ascii=False)
                    ) from exc
            if self.message_processor.continue_processing:
                self.processed = pd.concat([self.finish_process_chat(), self.processed], ignore_index=True)
            else:
                self.skipped_chats += 1
                self.skipped_chat_ids.append(self.chat_info['chat_id'])
            processed_num += 1
            self.update_progress(100 * processed_num / chats_len)
            chat.clear()

    @abstractmethod
    def start_process_chat(self, chat):
        pass

    @abstractmethod
    def finish_process_chat(self):
        pass
