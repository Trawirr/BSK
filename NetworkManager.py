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
            if True:  #ready_to_read:  # If there is a connection request
                conn, addr = self.server_socket.accept()
                if self.client_socket is None:
                    print(f"Connection accepted from {addr}")
                    self.client_socket = conn  # Set the client_socket attribute
                    self.generate_keys()

                    # Sending client's public key
                    self.client_socket.send(self.key_manager.public.publickey().export_key(format='PEM'))

                    # Receiving encrypted session key
                    session_key = self.client_socket.recv(1024)
                    self.key_manager.session_key = self.key_manager.decrypt_session_key(session_key)
                    self.key_manager.generate_aes()

                    print("Received session key:", self.key_manager.session_key)

                    self.is_connected = True
                    self.chat_app.gui_manager.start_receiving()

                    # self.key_manager.friends_public, self.key_manager.session_key = self.receive_key()

                    # if self.key_manager.friends_public is not None and self.key_manager.session_key is not None:
                    #     print(f"-- Public key --\n{self.key_manager.friends_public}")
                    #     print(f"-- Session key --\n{self.key_manager.session_key}")
                    #     self.is_connected = True
                    #     self.chat_app.gui_manager.start_receiving()
                    # else:
                    #     self.client_socket.close()
                    #     self.client_socket = None
                else:
                    conn.close()
            else:  # If there was no connection request within 2 seconds
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

                print("Received client's public key:", self.key_manager.friends_public)

                # Sending encrypted session key
                self.client_socket.sendall(self.key_manager.encrypt_session_key())
                
                print("Encrypted session key sent, decrypted session key:", self.key_manager.session_key)

                #self.send_keys()
                self.is_connected = True
                self.chat_app.gui_manager.start_receiving()
            except (ConnectionRefusedError, socket.timeout):  # Also catch the timeout exception
                print("Connection failed. Retrying in 2 seconds...")
                self.client_socket = None

    def generate_keys(self):
        self.key_manager = KeyManager()
        self.key_manager.generate_rsa(self.prk, self.puk)
        #self.key_manager.save_rsa()
        self.key_manager.generate_aes()

    # def send_keys(self):
    #     print("sending public key")
    #     self.client_socket.send(self.key_manager.public.publickey().export_key(format='PEM', passphrase=None, pkcs=1))
    #     time.sleep(1)  # Add a small delay before sending the session key
    #     print("sending session key")
    #     self.client_socket.sendall(self.key_manager.session_key)

    # def receive_key(self):
    #     print("Trying to receive public key...")
    #     public_key = self.client_socket.recv(4096)
    #     print("Public key received.", public_key)

    #     print("Trying to receive session key...")
    #     session_key = self.client_socket.recv(1024) 
    #     print("Session key received.", session_key)

    #     self.key_manager.generate_aes(session_key)

    #     return public_key, session_key

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
                self.client_socket.settimeout(1)  # Set a timeout of 5 seconds
                message = self.key_manager.decrypt_message(self.client_socket.recv(self.buffer_size)).decode()

                if self.is_file(message):
                    print("File sending started")
                    self.receive_file(message)

                if message:
                    print("Received message:", message)
                    return message
                else:
                    print("No message received.")
            except socket.timeout:
                print("Timeout: No message received.")
            except socket.error as e:
                print("Error receiving message:", str(e))
        else:
            print("No client connection established.")
        return None
    
    def is_file(self, message: str):
        if message.startswith("<START>") and len(message.split()) == 3:
            return True
        return False

    def send_file(self, file_path):
        file_name = file_path.split('/')[-1]
        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            data = f.read()

        self.send_message(f"<START> {file_name} {file_size}")
        time.sleep(1)

        chunk_size = 1024 - 32
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
                print(f"Progress: {progress:.2f}%")

            # End tag
            self.send_message("<END>")

    def receive_file(self, file_info):
        self.sending_file = True
        time.sleep(2)
        _, file_name, file_size = file_info.split()
        with open(f"files/{file_name}", 'wb') as file:
            print("open file")
            done = False
            file_bytes = b""
            while not done:
                received_data = self.client_socket.recv(1024)
                print(len(received_data))
                print(received_data)
                data = self.key_manager.decrypt_message(received_data)
                print(data,'\n')
                if file_bytes[-5:] == b"<END>":
                    done = True
                else:
                    file_bytes += data
                print(f"file bytes: {len(file_bytes)}")

            file.write(file_bytes)
        self.sending_file = False
        print("end")