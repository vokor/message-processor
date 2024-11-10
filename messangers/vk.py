import glob
import os
import re

from processors import Processor
from utils import Platform, read_html_file
from bs4 import BeautifulSoup

class VkProcessor(Processor):
    def __init__(self, data, custom_target_user_id):
        super().__init__(Platform.VK, custom_target_user_id)
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
        self.user_id_mapper = 1
        self.process_chats(self.parse_index())

    def start_process_chat(self, chat, user_id_mapper):
        def extract_number_from_filename(filepath):
            match = re.search(r'messages(\d+)\.html', filepath)
            if match:
                return int(match.group(1))
            return float('inf')

        chat_folder_path = self.data + '/messages/' + chat['id']
        if chat['id'] == '240400996':
            chat_paths = glob.glob(os.path.join(chat_folder_path, '*.html'))
            for path in sorted(chat_paths, key=extract_number_from_filename):
                file_data = read_html_file(path)
                soup = BeautifulSoup(file_data, 'html.parser')
                chat['messages'] = soup.find_all('div', class_='message')
                a = 1

    def finish_process_chat(self):
        pass