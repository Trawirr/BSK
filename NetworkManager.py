import select
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
        self.server_thread = threading.Thread(target=self.accept_connection_try_connect)
        self.server_thread.start()

    @property
    def info(self):
        print(f"""
        my socket: {self.server_socket}
        client socket: {self.client_socket}
        """)

    def accept_connection_try_connect(self):
        while not self.is_connected:
            print("connecting 1")
            
            # This line checks if there is a connection request within 2 seconds.
            ready_to_read, _, _ = select.select([self.server_socket], [], [], 2.0)
            
            if ready_to_read:  # If there is a connection request
                conn, addr = self.server_socket.accept()
                print('test2')
                if self.client_socket is None:
                    print("connecting 2")
                    print(f"Connection accepted from {addr}")
                    self.client_socket = conn  # Set the client_socket attribute
                    self.is_connected = True
                else:
                    conn.close()
                print('test')
            else:  # If there was no connection request within 2 seconds
                print("No connection request in last 2 seconds.")
                # Run your other method here
                self.connect()


    def connect(self):
        if self.client_socket is None:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.settimeout(2.0)  # Set a timeout of 2 seconds
                self.client_socket.connect(("localhost", self.client_port))
                print("Connected to", self.client_socket)
                self.is_connected = True
            except (ConnectionRefusedError, socket.timeout):  # Also catch the timeout exception
                print("Connection failed. Retrying in 2 seconds...")
                self.client_socket = None



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