import tkinter as tk


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
                self.log.configure(state='disabled')
            if ok:
                self.log.insert(tk.END, f"{command_name}: OK\n\n")
        return wrapper

    return catch_error


def read_file(filename):
    with open(filename, "r") as f:
        return f.read()
