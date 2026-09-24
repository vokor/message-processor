import re
import json

import emoji
import pandas as pd

from data_extractor import MessageProcessor
from processors import Processor
from utils import MessageType, DEFAULT_VALUE, Platform, DEFAULT_VALUE_NUM


class _RichMessageParser:
    """Read Telegram Desktop's rich_message JSON into legacy text parts.

    Schema: telegramdesktop/tdesktop, export/output/export_output_json.cpp
    (SerializeRichMessage, SerializeRichBlock and SerializeRichText), checked
    against commit e9399834de9ea53621ae12cd8d5ddf0b5b4d7950.
    Formatting adds no characters. Only content fields are traversed; IDs,
    paths, previews, callback data and old versions of text are not counted.
    """

    _TEXT_WRAPPERS = {
        'bold', 'italic', 'underline', 'strikethrough', 'code', 'subscript',
        'superscript', 'marked', 'spoiler', 'mention', 'hashtag', 'bot_command',
        'cashtag', 'link', 'email', 'phone', 'bank_card', 'anchor',
        'mention_name', 'formatted_date', 'diff',
    }
    _TEXT_BLOCKS = {'heading', 'paragraph', 'footer', 'thinking', 'code'}

    def __init__(self, rich_message):
        self.parts = []
        self.picture_count = 0
        self.video_count = 0
        self.seconds_count = 0
        self.sticker_emojis = []
        if not isinstance(rich_message, dict):
            raise ValueError('Telegram rich_message must be an object')
        self._blocks(rich_message['blocks'])

    def _string(self, value):
        if not isinstance(value, str):
            raise ValueError('Telegram rich message text must be a string')
        self.parts.append(value)

    def _url(self, value):
        if not isinstance(value, str):
            raise ValueError('Telegram rich message URL must be a string')
        # Match the legacy rule: count href links, but not href characters.
        self.parts.append({'text': '', 'href': value})

    def _text(self, node):
        if not isinstance(node, dict):
            raise ValueError('Telegram rich text must be an object')
        kind = node.get('type')
        if kind == 'empty':
            return
        if kind in {'plain', 'custom_emoji'}:
            self._string(node['text'])
        elif kind == 'concat':
            children = node['text']
            if not isinstance(children, list):
                raise ValueError('Telegram rich concat text must be an array')
            for child in children:
                self._text(child)
        elif kind in self._TEXT_WRAPPERS:
            self._text(node['text'])
        elif kind == 'text_link':
            self._text(node['text'])
            self._url(node['href'])
        elif kind == 'math':
            # There is no plain rendered formula in the export. Use its
            # textual source, without introducing formatting delimiters.
            self._string(node['source'])
        elif kind == 'inline_image':
            self.picture_count += 1
            self._document(node)
        elif kind == 'button':
            self._button(node)
        else:
            raise ValueError(f'Unsupported Telegram rich text type: {kind!r}')

    def _caption(self, node):
        # Media captions contain two RichText objects. Quote captions are
        # themselves RichText and are handled in the quote branch below.
        caption = node.get('caption')
        if caption is not None:
            if not isinstance(caption, dict):
                raise ValueError('Telegram rich media caption must be an object')
            for key in ('text', 'credit'):
                if key in caption:
                    self._text(caption[key])

    def _document(self, node, video_block=False):
        media_type = node.get('media_type')
        if media_type == 'video_file' or (video_block and media_type is None):
            self.video_count += 1
        duration = node.get('duration_seconds', 0)
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise ValueError('Telegram rich media duration must be a number')
        self.seconds_count += duration
        if 'sticker_emoji' in node:
            value = node['sticker_emoji']
            if not isinstance(value, str):
                raise ValueError('Telegram sticker_emoji must be a string')
            self.sticker_emojis.append(value)

    def _button(self, node):
        self._text(node['text'])
        action = node['button']
        if not isinstance(action, dict):
            raise ValueError('Telegram rich button action must be an object')
        if action.get('type') in {'url', 'web_view', 'auth'}:
            if 'url' in action:
                self._url(action['url'])

    def _blocks(self, blocks):
        if not isinstance(blocks, list):
            raise ValueError('Telegram rich blocks must be an array')
        for block in blocks:
            self._block(block)

    def _content(self, node):
        content = node.get('content')
        if content == 'text':
            self._text(node['text'])
        elif content == 'blocks':
            self._blocks(node['blocks'])
        else:
            raise ValueError(f'Unsupported Telegram rich content: {content!r}')

    def _block(self, node):
        if not isinstance(node, dict):
            raise ValueError('Telegram rich block must be an object')
        kind = node.get('type')
        if kind in self._TEXT_BLOCKS:
            self._text(node['text'])
        elif kind == 'author_date':
            self._text(node['author'])
        elif kind in {'divider', 'anchor', 'channel'}:
            return
        elif kind == 'list':
            for item in node['items']:
                self._content(item)
        elif kind == 'quote':
            self._content(node)
            if 'caption' in node:
                self._text(node['caption'])
        elif kind == 'photo':
            # A photo still exists if its file was excluded from the export.
            self.picture_count += 1
            if 'url' in node:
                self._url(node['url'])
            self._caption(node)
        elif kind in {'video', 'audio', 'file'}:
            self._document(node, video_block=(kind == 'video'))
            self._caption(node)
        elif kind == 'cover':
            self._block(node['block'])
        elif kind in {'embed', 'embed_post'}:
            if 'url' in node:
                self._url(node['url'])
            if kind == 'embed_post':
                self._blocks(node['blocks'])
            self._caption(node)
        elif kind in {'collage', 'slideshow'}:
            self._blocks(node['items'])
            self._caption(node)
        elif kind == 'math':
            self._string(node['formula'])
        elif kind == 'table':
            self._text(node['title'])
            for row in node['rows']:
                for cell in row['cells']:
                    if 'text' in cell:
                        self._text(cell['text'])
        elif kind == 'details':
            self._text(node['title'])
            self._blocks(node['blocks'])
        elif kind == 'related_articles':
            self._text(node['title'])
            for article in node['articles']:
                for key in ('title', 'description', 'author'):
                    if key in article:
                        self._string(article[key])
                self._url(article['url'])
        elif kind in {'map', 'input_map'}:
            self._caption(node)
        elif kind == 'button_row':
            for button in node['buttons']:
                self._button(button)
        else:
            # Never turn unknown content into a silently empty message.
            raise ValueError(f'Unsupported Telegram rich block type: {kind!r}')


class TelegramMessageProcessor(MessageProcessor):
    def __init__(self, user_id_mapper):
        super().__init__(user_id_mapper)
        self.prev_date_unixtime = 0

    def get_timestamp(self):
        return int(self.message['date_unixtime'])

    def get_message_type(self):
        if self.message.get('media_type', '') == 'voice_message':
            return MessageType.MESSAGE_VOICE
        elif self.message.get('media_type', '') == 'video_message':
            return MessageType.MESSAGE_VIDEO
        elif self.message.get('action', '') == 'phone_call':
            return MessageType.CALL_AUDIO
        else:
            return MessageType.MESSAGE

    def get_symbols_count(self):
        return self.message_structure['symbols_count']

    def get_picture_count(self):
        return (1 if len(self.message.get('photo', '')) > 0 else 0) + self.message_structure.get('picture_count', 0)

    def get_emoji_count(self):
        return self.message_structure['emoji_count']

    def get_link_count(self):
        return self.message_structure['links_count']

    def get_seconds_count(self):
        return self.message.get('duration_seconds', 0) + self.message_structure.get('seconds_count', 0)

    def get_video_count(self):
        return (1 if self.message.get('media_type', '') == 'video_file' else 0) + self.message_structure.get('video_count', 0)

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

        rich_message = None
        if 'rich_message' in self.message:
            rich_message = _RichMessageParser(self.message['rich_message'])
            message_text = rich_message.parts
        else:
            message_text = self.message['text']
        if isinstance(message_text, str):
            return {
                "symbols_count": count_symbols(message_text),
                "links_count": count_links(message_text),
                "emoji_count": count_emoji(message_text) + count_emoji(self.message.get('sticker_emoji', ''))
            }
        elif isinstance(message_text, list):
            symbols_count = 0
            links_count = 0
            emoji_count = 0
            for item in message_text:
                if isinstance(item, dict):
                    text = item.get("text", "")
                    symbols_count += count_symbols(text)
                    links_count += count_links(text) + count_links(item.get("href", ""))
                    emoji_count += count_emoji(text)
                else:
                    symbols_count += count_symbols(item)
                    links_count += count_links(item)
                    emoji_count += count_emoji(item)
            result = {
                "symbols_count": symbols_count,
                "links_count": links_count,
                "emoji_count": emoji_count
            }
            if rich_message is not None:
                result.update({
                    "picture_count": rich_message.picture_count,
                    "video_count": rich_message.video_count,
                    "seconds_count": rich_message.seconds_count,
                })
                result['emoji_count'] += count_emoji(self.message.get('sticker_emoji', ''))
                result['emoji_count'] += sum(count_emoji(value) for value in rich_message.sticker_emojis)
            return result
        else:
            raise ValueError(
                'Unsupported Telegram text value type: '
                + type(message_text).__name__
            )

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
        for value in self.user_id_mapper.values():
            return value

    def get_active_user_id(self):
        from_id = int(self.get_or_else('from_id', 'actor_id')[4:])
        return self.user_id_mapper.get(from_id, from_id)

    def get_active_user_nickname(self):
        return self.get_or_else('from', 'actor')

    def start(self):
        return

    def need_process_message(self):
        from_or_actor_id = self.get_or_else('from_id', 'actor_id')
        if from_or_actor_id is None:
            return False
        if 'channel' in from_or_actor_id:
            return False
        return self.message['type'] == 'message' or self.get_message_type() == MessageType.CALL_AUDIO

    def get_is_forwarded(self):
        return self.message.get('forwarded_from', DEFAULT_VALUE) != DEFAULT_VALUE


class TelegramProcessor(Processor):
    def __init__(self, data, custom_target_user_id, update_progress):
        super().__init__(Platform.TELEGRAM, custom_target_user_id, update_progress)
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

    def start_process_chat(self, chat):
        self.chat_info = {
            'chat_id': chat['id'],
            'chat_users_count': 2 if chat.get('type', DEFAULT_VALUE) == 'personal_chat' else -1,
        }
        if self.chat_info['chat_users_count'] == 2:
            self.chat_info['partner_used_id'] = chat['id']
            self.chat_info['partner_user_nickname'] = chat['name']
        else:
            self.chat_info['partner_used_id'] = DEFAULT_VALUE_NUM
            self.chat_info['partner_user_nickname'] = DEFAULT_VALUE
        return TelegramMessageProcessor(self.user_id_mapper)

    def finish_process_chat(self):
        messages = self.message_processor.data
        if len(messages) == 0:
            return pd.DataFrame()
        if self.chat_info['chat_users_count'] == -1:
            self.chat_info['chat_users_count'] = len(set(messages['active_user_id']))
        data = {key: [value] * len(next(iter(messages.values()))) for key, value in self.chat_info.items()}
        data.update(messages)
        return pd.DataFrame(data)
