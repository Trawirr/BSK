import select
import socket
import threading
import time
from KeyManager import KeyManager
from Cryptodome.PublicKey import RSA

class NetworkManager:
    def __init__(self, my_port, second_port, buffer_size, chat_app):
        self.chat_app = chat_app
        self.buffer_size = buffer_size
        self.client_port = second_port
        self.client_socket = None
        self.is_connected = False
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

                    self.key_manager.friends_public, self.key_manager.session_key = self.receive_key()

                    if self.key_manager.friends_public is not None and self.key_manager.session_key is not None:
                        print(f"-- Public key --\n{self.key_manager.friends_public}")
                        print(f"-- Session key --\n{self.key_manager.session_key}")
                        self.is_connected = True
                        self.chat_app.gui_manager.start_receiving()
                    else:
                        self.client_socket.close()
                        self.client_socket = None
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
                self.send_keys()
                self.is_connected = True
                self.chat_app.gui_manager.start_receiving()
            except (ConnectionRefusedError, socket.timeout):  # Also catch the timeout exception
                print("Connection failed. Retrying in 2 seconds...")
                self.client_socket = None

    def generate_keys(self):
        self.key_manager = KeyManager()
        self.key_manager.generate_rsa()
        self.key_manager.save_rsa()
        self.key_manager.generate_aes()

    def send_keys(self):
        print("sending public key")
        self.client_socket.send(self.key_manager.public.publickey().export_key(format='PEM', passphrase=None, pkcs=1))
        time.sleep(1)  # Add a small delay before sending the session key
        print("sending session key")
        self.client_socket.sendall(self.key_manager.session_key)

    def receive_key(self):
        print("Trying to receive public key...")
        public_key = self.client_socket.recv(4096)
        print("Public key received.", public_key)

        print("Trying to receive session key...")
        session_key = self.client_socket.recv(1024) 
        print("Session key received.", session_key)

        self.key_manager.generate_aes(session_key)

        return public_key, session_key

    def send_message(self, message):
        if self.client_socket is not None:
            try:
                self.client_socket.send(message.encode())
                print("Message sent:", message)
            except socket.error as e:
                print("Error sending message:", str(e))
        else:
            print("No client connection established.")

    def receive_message(self):
        print("receiving message... is connected:", self.is_connected)
        if self.client_socket is not None and self.is_connected:
            try:
                self.client_socket.settimeout(1)  # Set a timeout of 5 seconds
                message = self.client_socket.recv(self.buffer_size).decode()
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