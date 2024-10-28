from abc import ABC, abstractmethod
from collections import defaultdict


class MessageProcessor(ABC):
    def __init__(self):
        self.context = {}
        self.data = defaultdict(list)

    @abstractmethod
    def update_aggregated_chat_info(self, message):
        pass

    @abstractmethod
    def process(self, message):
        self.update_aggregated_chat_info(message)
        return {
            'partner_user_nickname': self.get_partner_user_nickname(),
            'partner_used_id': self.get_partner_used_id(),
            'active_user_id':
        }

    def get_aggregated_chat_info(self):
        return {
            'messenger_type': PLATFORM_TO_ID[self.context.name],
            'target_user_id': self.get_target_used_id(),
            'chat_id': context.chat_id,
            'chat_users_count': context.chat_users_count
        }


    @abstractmethod
    def get_target_used_id(self):
        pass

    @abstractmethod
    def get_partner_user_nickname(self):
        pass

    @abstractmethod
    def get_partner_used_id(self):
        pass



class TelegramMessageProcessor(MessageProcessor):
    def update_aggregated_chat_info(self, message):
        pass

    def process(self, message):
        pass

    def get_target_used_id(self):
        pass

    def get_partner_user_nickname(self):
        pass

    def get_partner_used_id(self):
        pass

    def start(self):
        return

    def parse(self):
        parsed_json = json.loads(self.data)
        print(len(parsed_json['chats']))