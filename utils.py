import hashlib
import tkinter as tk

DEFAULT_VALUE = 'nan'
DEFAULT_VALUE_NUM = -1
DEFAULT_TARGET_USER_NAME = "Вы"


class Platform:
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    VK = "vk"


class MessageType:
    MESSAGE = "0"
    MESSAGE_VIDEO = "1"  # кружочек
    MESSAGE_VOICE = "2"  # голосовое
    CALL_VIDEO = "3"  # видеозвонок
    CALL_AUDIO = "4"  # аудиозвонок
    CALL_UNDEFINED = "5"


PLATFORM_TO_ID = {
    Platform.TELEGRAM: 1,
    Platform.WHATSAPP: 2,
    Platform.VK: 3,
}


def get_hash(value):
    value_str = str(value)
    hash_object = hashlib.sha256(value_str.encode())
    hash_int = int(hash_object.hexdigest(), 16)
    scaled_value = hash_int % int(1e6)
    return scaled_value


def catch_command_errors(command_name):
    def catch_error(func):
        def wrapper(self, *args, **kwargs):
            ok = True
            try:
                func(self, *args, **kwargs)
            except Exception as e:
                ok = False
                self.log.insert(tk.END, f"Error while executing: {command_name}\n")
                self.log.insert(tk.END, str(e))
                self.process_button.config(state=tk.DISABLED)
                self.download_button.config(state=tk.DISABLED)
                self.upload_button.config(state=tk.DISABLED)
                self.selector.config(state=tk.DISABLED)
                self.user_id_entry.config(state=tk.DISABLED)
                self.log.configure(state='disabled')
            if ok:
                self.log.insert(tk.END, f"{command_name}: OK\n\n")

        return wrapper

    return catch_error


def read_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def read_html_file(filename):
    with open(filename, 'r', encoding='windows-1251') as file:
        return file.read()
