import tkinter as tk
from tkinter import filedialog
from tkinter import font

from utils import catch_command_errors, read_file, get_processor
from processors import Platform, TelegramProcessor, WhatsappProcessor

# class Application(tk.Frame):
#     def __init__(self, master=None):
#         super().__init__(master)
#         self.master = master
#         self.master.geometry('1010x700')
#         self.grid()
#         self.font = font.Font(size=14)
#         self.create_widgets()
#
#     def create_widgets(self):
#         self.selector_label = tk.Label(self, text="Мессенджер: ", font=self.font)
#         self.selector_label.grid(row=0, column=0, sticky="E")
#         self.var = tk.StringVar()
#         self.selector = tk.OptionMenu(self, self.var, Platform.VK, Platform.WHATSAPP, Platform.TELEGRAM)
#         self.selector.grid(row=0, column=1, sticky="W")
#         self.selector.config(width=20)
#
#         menu = self.selector.nametowidget(self.selector.cget('menu'))
#         for item in range(menu.index('end') + 1):
#             menu.entryconfig(item, font='Helvetica 18')
#
#         self.upload_button = tk.Button(self, text="Загрузить", command=self.upload_file, font=self.font, height=3, width=20)
#         self.upload_button.grid(row=1, column=0)
#
#         self.process_button = tk.Button(self, text="Обработать", command=self.process, state="disabled", font=self.font, height=3, width=20)
#         self.process_button.grid(row=2, column=0)
#
#         self.log = tk.Text(self, height=20, width=100, font=self.font)
#         self.log.grid(row=3, column=0, columnspan=2)
#
#         self.download_button = tk.Button(self, text="Скачать", command=self.download, state="disabled", font=self.font, height=3, width=20)
#         self.download_button.grid(row=4, column=0, columnspan=2)
#
#     @catch_command_errors("upload_file")
#     def upload_file(self):
#         filename = filedialog.askopenfilename()
#         self.data = read_file(filename)
#         self.download_button.config(state=tk.DISABLED)
#         self.process_button.config(state="normal")
#         self.log.insert(tk.END, f"File uploaded: {filename}\n")
#
#     @catch_command_errors("process")
#     def process(self):
#         platform = self.var.get()
#         if platform == "":
#             self.log.insert(tk.END, f"Platform is not specified\n")
#             return
#         self.log.insert(tk.END, f"Processing for platform: {platform}\n")
#         self.download_button.config(state="normal")
#         self.processor = get_processor(platform, self.data)
#         self.processor.parse()
#         self.processor.process()
#
#     @catch_command_errors("download")
#     def download(self):
#         self.log.insert(tk.END, f"Result file ready to download.\n")
#
#
# root = tk.Tk()
# root.title("Message processor")
# app = Application(master=root)
# app.mainloop()


data = read_file("/home/vladimir/Git/message-processor/result.json")
processor = TelegramProcessor(data)
chats = processor.parse()







