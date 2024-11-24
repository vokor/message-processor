import glob
import os
import re
import json
from datetime import datetime

import emoji
import pandas as pd

from data_extractor import MessageProcessor
from processors import Processor
from utils import MessageType, DEFAULT_VALUE, Platform, DEFAULT_VALUE_NUM, get_hash


class WhatsappMessageProcessor(MessageProcessor):
    def __init__(self, user_id_mapper):
        super().__init__(user_id_mapper)
        self.prev_date_unixtime = 0

    def sanitize_input(self, text):
        return ''.join(c for c in text if c.isprintable())

    def get_timestamp(self):
        sanitized_message = self.sanitize_input(self.message)

        patterns_formats = [
            (r'^\[(\d{1,2})\.(\d{1,2})\.(\d{4}), (\d{2}):(\d{2}):(\d{2})\]', '%d.%m.%Y, %H:%M:%S'),
            (r'^(\d{1,2})\.(\d{1,2})\.(\d{4}), (\d{2}):(\d{2}) -', '%d.%m.%Y, %H:%M'),
            (r'^(\d{1,2})/(\d{1,2})/(\d{2}), (\d{2}):(\d{2}) -', '%m/%d/%y, %H:%M'),
        ]
        for pattern, date_format in patterns_formats:
            match = re.match(pattern, sanitized_message)
            if match:
                if date_format == '%d.%m.%Y, %H:%M:%S':
                    timestamp_str = f"{match.group(1)}.{match.group(2)}.{match.group(3)}, {match.group(4)}:{match.group(5)}:{match.group(6)}"
                elif date_format == '%d.%m.%Y, %H:%M':
                    timestamp_str = f"{match.group(1)}.{match.group(2)}.{match.group(3)}, {match.group(4)}:{match.group(5)}"
                elif date_format == '%m/%d/%y, %H:%M':
                    timestamp_str = f"{match.group(1)}/{match.group(2)}/{match.group(3)}, {match.group(4)}:{match.group(5)}"
                dt = datetime.strptime(timestamp_str, date_format)
                return int(dt.timestamp())

        raise Exception("Can't parse timestamp from: " + str(self.message))

    def get_message_type(self):
        content = self.get_content()
        if content:
            if "Voice call" in content:
                return MessageType.CALL_AUDIO
            elif "Video call" in content:
                return MessageType.CALL_VIDEO
            elif ".opus>" in content:
                return MessageType.MESSAGE_VOICE
            elif ".mp4>" in content or ".mov>" in content:
                return MessageType.MESSAGE_VIDEO
            else:
                return MessageType.MESSAGE
        return MessageType.CALL_UNDEFINED

    def get_symbols_count(self):
        return self.message_structure['symbols_count']

    def get_picture_count(self):
        content = self.get_content()
        return int(bool(re.search(r'<attached:.*\.jpg>', content, re.IGNORECASE)))

    def get_emoji_count(self):
        return self.message_structure['emoji_count']

    def get_link_count(self):
        return self.message_structure['links_count']

    def get_seconds_count(self):
        content = self.get_content()
        match = re.search(r'(\d+) min', content)
        if match:
            return int(match.group(1)) * 60
        match = re.search(r'(\d+) sec', content)
        if match:
            return int(match.group(1))
        return 0

    def get_video_count(self):
        content = self.get_content()
        return int(bool(re.search(r'<attached:.*\.(mp4|mov)>', content, re.IGNORECASE)))

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

        message_text = self.get_content()
        return {
            "symbols_count": count_symbols(message_text),
            "links_count": count_links(message_text),
            "emoji_count": count_emoji(message_text)
        }

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
        return self.user_id_mapper

    def get_active_user_id(self):
        return get_hash(self.get_active_user_nickname())

    def get_content(self):
        match = re.search(r'[\]\-] .*?: (.*)', self.message)
        if match:
            return match.group(1)
        else:
            return ""

    def get_active_user_nickname(self):
        match = re.search(r'[\]\-] (.*?):', self.message)
        if match:
            return match.group(1)
        else:
            return ""

    def start(self):
        return

    def need_process_message(self):
        return True

    def get_is_forwarded(self):
        return False


class WhatsappProcessor(Processor):
    def __init__(self, data, custom_target_user_id, update_progress):
        super().__init__(Platform.WHATSAPP, custom_target_user_id, update_progress)
        self.data = data

    def get_chat_paths(self):
        link_list = []
        for filename in os.listdir(self.data):
            path = os.path.join(self.data, filename)
            link_list.append({
                'path': path,
                'id': get_hash(path),
                'name': filename,
                'messages': []
            })
        return link_list

    def run(self):
        self.user_id_mapper = 1
        self.process_chats(self.get_chat_paths())

    def sanitize_input(self, text):
        return ''.join(c for c in text if c.isprintable())

    def sanitize_input(self, text):
        # This function removes non-printable characters including Unicode marks
        return ''.join(c for c in text if c.isprintable())

    def get_messages(self, raw_data):
        # Updated patterns to allow one or two digits for day and month
        timestamp_patterns = [
            r'^\[\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}:\d{2}\]',  # [dd.mm.yyyy, hh:mm:ss]
            r'^\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2} -',          # dd.mm.yyyy, hh:mm -
            r'^\d{1,2}/\d{1,2}/\d{2}, \d{2}:\d{2} -'         # m/d/yy, hh:mm - (allows single-digit month and day)
        ]
        combined_pattern = '|'.join(timestamp_patterns)
        lines = raw_data.split('\n')
        messages = []
        current_message = []
        for line in lines:
            sanitized_line = self.sanitize_input(line).strip()
            if re.match(combined_pattern, sanitized_line):
                if current_message:
                    messages.append('\n'.join(current_message).strip())
                    current_message = []
            current_message.append(sanitized_line)
        if current_message:
            messages.append('\n'.join(current_message).strip())
        return messages

    def read_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def start_process_chat(self, chat, user_id_mapper):
        raw_data = self.read_file(chat['path'])
        chat['messages'] = self.get_messages(raw_data)
        self.chat_info = {
            'chat_id': int(chat['id']),
        }
        return WhatsappMessageProcessor(user_id_mapper)

    def finish_process_chat(self):
        messages = self.message_processor.data
        if len(messages) == 0:
            return pd.DataFrame()
        self.chat_info['chat_users_count'] = len(set(messages['active_user_id']))
        data = {key: [value] * len(next(iter(messages.values()))) for key, value in self.chat_info.items()}
        data.update(messages)
        return pd.DataFrame(data)