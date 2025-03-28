import platform
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from tkinter import font
import os
from math import log, pow
import time

from messangers.tg import TelegramProcessor
from messangers.vk import VkProcessor
from messangers.whatsapp import WhatsappProcessor
from utils import catch_command_errors, read_file, Platform, read_html_file


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"

    size_name = ("B", "KB", "MB", "GB", "TB", "PB")
    i = int(min(len(size_name) - 1, (log(size_bytes, 1024))))  # Use math.log
    p = pow(1024, i)  # Use math.pow
    s = round(size_bytes / p, 2)

    return f"{s} {size_name[i]}"


def get_processor(platform, data, user_id, update_progress):
    if platform == Platform.TELEGRAM:
        return TelegramProcessor(data, int(user_id), update_progress)
    elif platform == Platform.WHATSAPP:
        return WhatsappProcessor(data, int(user_id), update_progress)
    elif platform == Platform.VK:
        return VkProcessor(data, int(user_id), update_progress)
    else:
        raise Exception(f"Unknown platform: {platform}\n")

def get_reader(platform):
    if platform == Platform.TELEGRAM:
        return read_file
    elif platform == Platform.WHATSAPP:
        return lambda x: x
    elif platform == Platform.VK:
        return lambda x: x
    else:
        raise Exception(f"Unknown platform: {platform}\n")

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.geometry('1010x800')
        self.grid()
        self.font = font.Font(size=14)
        self.create_widgets()
        self.is_uploaded = False
        self.is_user_id_set = False
        os_type = platform.system()
        if os_type == "Windows":
            self.log.insert(tk.END, "Running on Windows\n")
        elif os_type == "Darwin":
            self.log.insert(tk.END, "Running on macOS\n")
        elif os_type == "Linux":
            self.log.insert(tk.END, "Running on Linux\n")

    def update_progress(self, value):
        self.progress['value'] = value
        self.update_idletasks()

    def create_widgets(self):
        self.selector_label = tk.Label(self, text="Мессенджер: ", font=self.font)
        self.selector_label.grid(row=0, column=0, sticky="E")
        self.var = tk.StringVar()
        self.selector = tk.OptionMenu(self, self.var, Platform.VK, Platform.WHATSAPP, Platform.TELEGRAM)
        self.selector.grid(row=0, column=1, sticky="W")
        self.selector.config(width=20)

        menu = self.selector.nametowidget(self.selector.cget('menu'))
        for item in range(menu.index('end') + 1):
            menu.entryconfig(item, font='Helvetica 18')

        self.user_id_var = tk.StringVar()
        self.user_id_var.trace_add('write', self.on_user_id_change)

        self.id_label = tk.Label(self, text="  ID: ", font=self.font)
        self.id_label.grid(row=1, column=0, sticky="E")

        self.user_id_entry = tk.Entry(self, textvariable=self.user_id_var, font=self.font)
        self.user_id_entry.grid(row=1, column=1, sticky="W")

        self.upload_button = tk.Button(self, text="Загрузить", command=self.upload_file, font=self.font, height=3,
                                       width=20)
        self.upload_button.grid(row=1, column=0)

        self.process_button = tk.Button(self, text="Обработать", command=self.process, state="disabled", font=self.font,
                                        height=3, width=20)
        self.process_button.grid(row=2, column=0)

        self.progress = ttk.Progressbar(self, orient='horizontal', length=400, mode='determinate')
        self.progress.grid(row=2, column=1, sticky='W', padx=10, pady=5)

        self.log = tk.Text(self, height=20, width=100, font=self.font)
        self.log.grid(row=3, column=0, columnspan=2)

        self.download_button = tk.Button(self, text="Скачать", command=self.download, state="disabled", font=self.font,
                                         height=3, width=20)
        self.download_button.grid(row=4, column=0, columnspan=2)

    @catch_command_errors("upload_file")
    def upload_file(self):
        if self.var.get() == Platform.VK or self.var.get() == Platform.WHATSAPP:
            filename = filedialog.askdirectory()
        else:
            filename = filedialog.askopenfilename()
            self.log.insert(tk.END, f"Try upload: {filename}\n")
            self.log.insert(tk.END, f"File size: {convert_size(os.path.getsize(filename))}\n")
        self.data = get_reader(self.var.get())(filename)
        self.download_button.config(state=tk.DISABLED)
        self.is_uploaded = True
        if self.is_uploaded and self.is_user_id_set:
            self.process_button.config(state="normal")
        self.log.insert(tk.END, f"File uploaded: {filename}\n")

    def on_user_id_change(self, *args):
        user_id = self.user_id_var.get()
        self.log.insert(tk.END, f"User ID changed to: {user_id}\n")
        if len(user_id) > 0:
            self.is_user_id_set = True
        else:
            self.is_user_id_set = False
        if self.is_uploaded and self.is_user_id_set:
            self.process_button.config(state="normal")
        else:
            self.process_button.config(state=tk.DISABLED)

    @catch_command_errors("process")
    def process(self):
        self.user_id_entry.config(state=tk.DISABLED)
        platform = self.var.get()
        user_id = self.user_id_entry.get().strip()
        if platform == "":
            self.log.insert(tk.END, f"Platform is not specified\n")
            return
        if not user_id:
            self.log.insert(tk.END, "User ID is not specified\n")
            return
        self.log.insert(tk.END, f"Processing for platform: {platform} with User ID: {user_id}\n")
        self.download_button.config(state="normal")
        start_time = time.time()
        self.processor = get_processor(platform, self.data, user_id, self.update_progress)
        self.processor.run()
        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        self.log.insert(tk.END, f"Execution time: {minutes} min {seconds} sec\n")
        self.log.insert(tk.END, f"Processed chats: {self.processor.all_chats}, skipped chats: {self.processor.skipped_chats}, skipped chat ids: {self.processor.skipped_chat_ids}\n")

    @catch_command_errors("download")
    def download(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.processor.processed.to_csv(file_path, index=False)
            self.log.insert(tk.END, f"File saved at {file_path}\n")

root = tk.Tk()
root.title("Message processor")
app = Application(master=root)
app.mainloop()

# data = read_file("/home/vladimir/Git/message-processor/result.json")
# processor = TelegramProcessor(data, 1)
# processor.run()
# processor.processed.to_csv('processed.csv', index=False)

# data = "/home/vladimir/Git/message-processor/data/vk"
# processor = VkProcessor(data, 1)
# processor.run()
# processor.processed.to_csv('processed.csv', index=False)

# data = "/home/vladimir/Git/message-processor/data/whatsapp"
# processor = WhatsappProcessor(data, 1, lambda x: x)
# processor.run()
# processor.processed.to_csv('processed.csv', index=False)
