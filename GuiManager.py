import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import threading
import hashlib
import time

class GuiManager:

    def __init__(self, chat_app):
        self.chat_app = chat_app
        self.receive_thread = None

        self.root = tk.Tk()
        self.root.title('Secure Chat App')

        self.frame = ttk.Frame(self.root, padding='10')
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.text_field = ttk.Entry(self.frame, width=50)
        self.text_field.grid(row=0, column=0, padx=(0, 10))

        self.send_button = ttk.Button(self.frame, text='Send', command=self.send_message)
        self.send_button.grid(row=0, column=1)

        self.file_button = ttk.Button(self.frame, text='Send File', command=self.send_file)
        self.file_button.grid(row=0, column=2, padx=(10, 0))

        self.text_area = tk.Text(self.frame, width=50, height=15)
        self.text_area.grid(row=1, column=0, columnspan=3, pady=(10, 0))

        #self.status_button = ttk.Button(self.frame, text='Refresh', command=self.update_status)
        #self.status_button.grid(row=2, column=0, columnspan=3, pady=(10, 0))

        self.status_label = ttk.Label(self.frame, text='Disconnected')
        self.status_label.grid(row=3, column=0, columnspan=3, pady=(10, 0))

        self.progress = ttk.Progressbar(self.frame, mode='determinate')
        self.progress.grid(row=4, column=0, columnspan=3, pady=(10, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def run(self):
        username = self.ask_username()
        password = self.ask_password()

        # Hashing the username and password.
        if username is not None:
            username_hash = hashlib.sha256(username.encode()).hexdigest()
        else:
            username_hash = None

        if password is not None:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
        else:
            password_hash = None

        self.chat_app.set_login_details(username_hash, password_hash)
        self.status_thread = threading.Thread(target=self.update_status)
        self.status_thread.daemon = True
        self.status_thread.start()
        self.root.mainloop()

    def start_receiving(self):
        if not self.receive_thread:
            print("Receiving messages started")
            self.receive_thread = threading.Thread(target=self.receive_messages_background)
            self.receive_thread.daemon = True
            self.receive_thread.start()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()

    def receive_messages_background(self):
        while True:
            if not self.chat_app.network_manager.sending_file:
                #print("start", self.chat_app.network_manager.sending_file)
                msg = self.chat_app.network_manager.receive_message()
                if msg:
                    self.display_message("Friend: " + msg)
            time.sleep(1)
            #print("end")

    def send_message(self):
        message = self.text_field.get()
        if message and not self.chat_app.network_manager.sending_file:
            message = message + " "
            self.chat_app.network_manager.send_message(message)
            self.display_message(f"You: {message}")
            self.text_field.delete(0, tk.END)

    def send_file_background(self):
        self.chat_app.network_manager.send_file(self.file_path)

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path = file_path
            
            self.send_file_thread = threading.Thread(target=self.send_file_background)
            self.send_file_thread.daemon = True
            self.send_file_thread.start()

    def update_status(self):
        if self.chat_app.network_manager.is_connected: 
            self.status_label['text'] = "Connected"
        else:
            self.status_label['text'] = "Disconnected"
            self.chat_app.network_manager.connect()
        self.root.after(1000, self.update_status)

    def update_progress(self, value):
        self.progress['value'] = value

    def display_message(self, message):
        self.text_area.insert(tk.END, message + '\n')

    def display_error(self, error):
        messagebox.showerror('Error', error)

    def ask_password(self):
        password = tk.simpledialog.askstring("Password", "Enter password:", show='*')
        return password
    
    def ask_username(self):
        username = tk.simpledialog.askstring("Username", "Enter username:")
        return username
