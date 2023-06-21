import socket
import threading
import time
import os
from KeyManager import KeyManager

class NetworkManager:
    def __init__(self, my_port, second_port, buffer_size, chat_app, prk, puk):
        self.chat_app = chat_app
        self.buffer_size = buffer_size
        self.client_port = second_port
        self.prk = prk
        self.puk = puk
        self.client_socket = None
        self.is_connected = False
        self.sending_file = False
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("localhost", my_port))
        self.server_socket.listen(1)
        self.server_thread = threading.Thread(target=self.accept_connection_try_connect)
        self.server_thread.daemon = True
        self.server_thread.start()

        self.key_manager = None

    @property
    def info(self):
        print(f"""
        my socket: {self.server_socket}
        client socket: {self.client_socket}
        """)

    def accept_connection_try_connect(self):
        while not self.is_connected:
            if True:
                conn, addr = self.server_socket.accept()
                if self.client_socket is None:
                    print(f"Connection accepted from {addr}")
                    self.client_socket = conn
                    self.generate_keys()

                    # Sending client's public key
                    self.client_socket.send(self.key_manager.public.publickey().export_key(format='PEM'))

                    # Receiving encrypted session key
                    session_key = self.client_socket.recv(1024)
                    self.key_manager.session_key = self.key_manager.decrypt_session_key(session_key)
                    self.key_manager.generate_aes()

                    # print("Received session key:", self.key_manager.session_key)
                    
                    print("Session key:", self.key_manager.session_key)

                    self.is_connected = True
                    self.chat_app.gui_manager.start_receiving()
                else:
                    conn.close()
            else:
                print("No connection request in last 2 seconds.")
                self.connect()


    def connect(self):
        time.sleep(5)
        if self.client_socket is None:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(2.0)  # Set a timeout of 2 seconds
                self.client_socket.connect(("localhost", self.client_port))
                print("Connected to", self.client_socket)
                self.generate_keys()

                # Receiving client's public key
                friends_public_key = self.client_socket.recv(4096)
                self.key_manager.friends_public = friends_public_key

                # Sending encrypted session key
                self.client_socket.sendall(self.key_manager.encrypt_session_key())

                print("Session key:", self.key_manager.session_key)
                self.is_connected = True
                self.chat_app.gui_manager.start_receiving()
            except (ConnectionRefusedError, socket.timeout):
                print("Connection failed. Retrying in 2 seconds...")
                self.client_socket = None

    def generate_keys(self):
        self.key_manager = KeyManager()
        self.key_manager.generate_rsa(self.prk, self.puk)
        self.key_manager.generate_aes()

    def send_message(self, message):
        if self.client_socket is not None:
            try:
                self.client_socket.send(self.key_manager.encrypt_message(message.encode()))
                print("Message sent:", message)
            except socket.error as e:
                print("Error sending message:", str(e))
        else:
            print("No client connection established.")

    def receive_message(self):
        if self.client_socket is not None and self.is_connected and not self.sending_file:
            try:
                self.client_socket.settimeout(1)
                message = self.key_manager.decrypt_message(self.client_socket.recv(self.buffer_size)).decode()

                if self.is_file(message):
                    print("File sending started")
                    self.chat_app.gui_manager.display_message(f"Friend: sending file: {message.split('|')[1]}")
                    self.receive_file(message)

                elif message:
                    print("Received message:", message)
                    return message
                else:
                    print("No message received.")
            except socket.timeout:
                pass
            except socket.error as e:
                print("Error receiving message:", str(e))
                self.client_socket = None
                self.is_connected = False
                self.chat_app.gui_manager.display_message(f"-- DISCONNECTED --")
        else:
            print("No client connection established.")
        return None
    
    def is_file(self, message: str):
        if message.startswith("<START>") and len(message.split('|')) == 3:
            return True
        return False

    def send_file(self, file_path):
        self.sending_file = True
        self.client_socket.settimeout(5)
        file_name = file_path.split('/')[-1]
        self.chat_app.gui_manager.display_message(f"You: sending file: {file_name}")
        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            data = f.read()

        self.send_message(f"<START>|{file_name}|{file_size}")
        time.sleep(1)

        chunk_size = 1024*1024 - 32
        bytes_sent = 0

        with open(file_path, "rb") as f:
            while True:
                # Read chunk from file
                data = f.read(chunk_size)
                if not data:
                    break
                    
                # Encrypt the chunk
                encrypted = self.key_manager.encrypt_message(data)
                
                # Send encrypted chunk
                self.client_socket.sendall(encrypted)
                
                # Update the amount of bytes sent
                bytes_sent += len(data)
                
                # Print progress
                progress = (bytes_sent / file_size) * 100
                self.chat_app.gui_manager.update_progress(progress)
                print(f"Progress: {progress:.2f}%")

        self.sending_file = False

    def receive_file(self, file_info):
        self.sending_file = True
        time.sleep(2)
        self.client_socket.settimeout(5)
        _, file_name, file_size = file_info.split('|')
        file_size = int(file_size)
        with open(f"files/{file_name}", 'wb') as file:
            file_bytes = b""
            while True:
                received_data = self.client_socket.recv(1024*1024)
                data = self.key_manager.decrypt_message(received_data)
                file_bytes += data
                progress = (len(file_bytes) / file_size) * 100
                print(f"Progress: {progress:.2f}%")
                self.chat_app.gui_manager.update_progress(progress)
                if len(file_bytes) == file_size:
                    break

            file.write(file_bytes)
        self.sending_file = False