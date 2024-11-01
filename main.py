import json
import tkinter as tk
from tkinter import filedialog
from tkinter import font

from utils import catch_command_errors, read_file
from processors import Platform, TelegramProcessor


def get_processor(platform, data, user_id):
    if platform == Platform.TELEGRAM:
        return TelegramProcessor(data, int(user_id))
    elif platform == Platform.WHATSAPP:
        raise Exception("Not implemented")
    elif platform == Platform.VK:
        raise Exception("Not implemented")
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

        self.id_label = tk.Label(self, text="User ID: ", font=self.font)
        self.id_label.grid(row=1, column=0, sticky="E")

        self.user_id_entry = tk.Entry(self, textvariable=self.user_id_var, font=self.font)
        self.user_id_entry.grid(row=1, column=1, sticky="W")

        self.upload_button = tk.Button(self, text="Загрузить", command=self.upload_file, font=self.font, height=3,
                                       width=20)
        self.upload_button.grid(row=1, column=0)

        self.process_button = tk.Button(self, text="Обработать", command=self.process, state="disabled", font=self.font,
                                        height=3, width=20)
        self.process_button.grid(row=2, column=0)

        self.log = tk.Text(self, height=20, width=100, font=self.font)
        self.log.grid(row=3, column=0, columnspan=2)

        self.download_button = tk.Button(self, text="Скачать", command=self.download, state="disabled", font=self.font,
                                         height=3, width=20)
        self.download_button.grid(row=4, column=0, columnspan=2)

    @catch_command_errors("upload_file")
    def upload_file(self):
        filename = filedialog.askopenfilename()
        self.data = read_file(filename)
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
        self.processor = get_processor(platform, self.data, user_id)
        self.processor.run()

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
