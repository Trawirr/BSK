from NetworkManager import *
from GuiManager import *
from Cryptodome.PublicKey import RSA

def generate_rsa_keys():
    # Generate RSA key pair
    key = RSA.generate(2048)

    # Export private key to PEM format
    private_key = key.export_key()

    # Export public key to PEM format
    public_key = key.publickey().export_key()

    return private_key, public_key

class ChatApp:
    def __init__(self, my_port, second_port):
        self.network_manager = NetworkManager(my_port=my_port, second_port=second_port, buffer_size=1024)
        self.gui_manager = GuiManager(self)

        self.gui_manager.run()

if __name__ == "__main__":
    my_port = int(input("What's your port: "))
    second_port = int(input("What's the second port: "))
    pr, pu = generate_rsa_keys()
    ca = ChatApp(my_port, second_port)