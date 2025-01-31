import glob
import os
import re
from datetime import datetime

import emoji
import pandas as pd

from data_extractor import MessageProcessor
from processors import Processor
from utils import Platform, read_html_file, DEFAULT_TARGET_USER_NAME, MessageType, DEFAULT_VALUE_NUM, DEFAULT_VALUE
from bs4 import BeautifulSoup

class VkMessageProcessor(MessageProcessor):
    def __init__(self, user_id_mapper):
        self.OK = False
        self.time = None
        super().__init__(user_id_mapper)
        self.prev_date_unixtime = 0

    def get_timestamp(self):
        if self.time is not None:
            return self.time

        month_map = {
            'янв': 'Jan',
            'фев': 'Feb',
            'мар': 'Mar',
            'апр': 'Apr',
            'май': 'May',
            'мая': 'May',
            'июн': 'Jun',
            'июл': 'Jul',
            'авг': 'Aug',
            'сен': 'Sep',
            'окт': 'Oct',
            'ноя': 'Nov',
            'дек': 'Dec'
        }

        pattern = r'\d{1,2} [а-яё]+ \d{4} в \d{1,2}:\d{2}:\d{2}'
        header = self.message.find('div', class_='message__header').text
        date_str = header.split(', ')[-1]
        match = re.search(pattern, date_str)

        if match:
            date_part = match.group()

            for ru_month, en_month in month_map.items():
                if ru_month in date_part:
                    date_part = date_part.replace(ru_month, en_month).replace(' в ', ' ')
                    break

            try:
                dt = datetime.strptime(date_part, "%d %b %Y %H:%M:%S")
                t = int(dt.timestamp())
                self.time = t
                return t
            except ValueError:
                raise Exception(f"Error: couldn't parse date: {date_part}")
        else:
            raise Exception(f"Error: couldn't match date pattern in: {header}")


    def check_if_call(self):
        attachment_description = self.message.find('div', class_='attachment__description')
        if attachment_description and 'Звонок' in attachment_description.text:
            return True
        return False

    def check_if_video(self):
        image_count = 0
        attachment_descriptions = self.message.find_all('div', class_='attachment__description')
        for description in attachment_descriptions:
            if 'Видеозапись' in description.text:
                image_count += 1
        return image_count

    def check_if_voice(self):
        attachment_link = self.message.find('a', class_='attachment__link')
        if attachment_link and attachment_link['href'].endswith('.ogg'):
            return True
        return False

    def get_message_type(self):
        if self.check_if_voice():
            return MessageType.MESSAGE_VOICE
        elif self.check_if_video():
            return MessageType.MESSAGE_VIDEO
        elif self.check_if_call():
            return MessageType.CALL_AUDIO
        else:
            return MessageType.MESSAGE

    def get_symbols_count(self):
        return self.message_structure['symbols_count']

    def get_picture_count(self):
        image_count = 0
        attachment_descriptions = self.message.find_all('div', class_='attachment__description')
        for description in attachment_descriptions:
            if 'Фотография' in description.text:
                image_count += 1
        return image_count

    def get_emoji_count(self):
        return self.message_structure['emoji_count']

    def get_link_count(self):
        return self.message_structure['links_count']

    def get_seconds_count(self):
        return DEFAULT_VALUE_NUM

    def get_video_count(self):
        return 1 if self.check_if_video() else 0

    def get_message_text(self):
        header_div = self.message.find('div', class_='message__header')
        message_text_div = header_div.find_next_sibling('div')
        text_parts = [element for element in message_text_div.contents if element.name != 'div']
        message_text = ''.join(str(part) for part in text_parts).strip()
        return message_text

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

        message_text = self.get_message_text()
        return {
            "symbols_count": count_symbols(message_text),
            "links_count": count_links(message_text),
            "emoji_count": count_emoji(message_text) + count_emoji(self.message.get('sticker_emoji', ''))
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
        header = self.message.find('div', class_='message__header')
        if header.find('a'):
            href = header.find('a')['href']
            return int(re.split('id|public|club', href)[-1])
        else:
            return self.get_target_used_id()

    def get_active_user_nickname(self):
        header = self.message.find('div', class_='message__header')
        if header.find('a'):
            return header.find('a').text
        else:
            return DEFAULT_TARGET_USER_NAME

    def start(self):
        return

    def need_process_message(self):
        return True

    def get_is_forwarded(self):
        attachment_description = self.message.find('div', class_='attachment__description')
        if attachment_description and 'прикреплён' in attachment_description.text:
            return True
        return False


class VkProcessor(Processor):
    def __init__(self, data, custom_target_user_id, update_progress):
        super().__init__(Platform.VK, custom_target_user_id, update_progress)
        self.data = data

    def parse_index(self):
        index_messages = read_html_file(self.data + '/messages/index-messages.html')
        soup = BeautifulSoup(index_messages, 'html.parser')
        link_pairs = []
        for item in soup.find_all('div', class_='item'):
            link_tag = item.find('a')
            if link_tag:
                href = link_tag.get('href').split('/')[0]
                text = link_tag.text
                link_pairs.append({
                    'id': href,
                    'name': text,
                    'messages': []
                })
        return link_pairs

    def run(self):
        self.user_id_mapper = self.custom_target_user_id
        self.process_chats(self.parse_index())

    def start_process_chat(self, chat, user_id_mapper):
        def extract_number_from_filename(filepath):
            match = re.search(r'messages(\d+)\.html', filepath)
            if match:
                return int(match.group(1))
            return float('inf')

        def message_generator(chat_folder_path):
            chat_paths = glob.glob(os.path.join(chat_folder_path, '*.html'))
            for path in sorted(chat_paths, key=extract_number_from_filename, reverse=True):
                file_data = read_html_file(path)
                soup = BeautifulSoup(file_data, 'html.parser')
                for message in soup.find_all('div', class_='message'):
                    yield message

        self.chat_info = {
            'chat_id': int(chat['id']),
        }
        chat_folder_path = self.data + '/messages/' + chat['id']
        #if chat['id'] == '2000000151':#'240400996':
        chat['messages'] = message_generator(chat_folder_path)
        return VkMessageProcessor(user_id_mapper)

    def finish_process_chat(self):
        messages = self.message_processor.data
        if len(messages) == 0:
            return pd.DataFrame()
        self.chat_info['chat_users_count'] = len(set(messages['active_user_id']))
        data = {key: [value] * len(next(iter(messages.values()))) for key, value in self.chat_info.items()}
        data.update(messages)
        return pd.DataFrame(data)