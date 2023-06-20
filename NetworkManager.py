import socket
import threading

class NetworkManager:
    def __init__(self, my_port, second_port, buffer_size):
        self.buffer_size = buffer_size
        self.client_port = second_port
        self.client_socket = None
        self.is_connected = False
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("localhost", my_port))
        self.server_socket.listen(1)
        self.server_thread = threading.Thread(target=self.accept_connection)
        self.server_thread.start()

    @property
    def info(self):
        print(f"""
        my socket: {self.server_socket}
        client socket: {self.client_socket}
        """)

    def accept_connection(self):
        while not self.is_connected:
            print("connecting 1")
            conn, addr = self.server_socket.accept()
            if self.client_socket is None:
                print("connecting 2")
                print(f"Connection accepted from {addr}")
                self.client_socket = conn  # Set the client_socket attribute
                self.is_connected = True
            else:
                conn.close()

    def connect(self):
        if self.client_socket is None:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect(("localhost", self.client_port))
                print("Connected to", self.client_socket)
                self.is_connected = True
            except ConnectionRefusedError:
                print("Connection failed. Retrying in 5 seconds...")

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
        if self.client_socket is not None:
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