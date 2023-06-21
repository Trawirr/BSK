import os
import hashlib

def import_crypto_module(module_name):
    try:
        module = __import__(f'Cryptodome.{module_name}', fromlist=[module_name])
    except ImportError:
        try:
            module = __import__(f'Crypto.{module_name}', fromlist=[module_name])
        except ImportError:
            raise ImportError(f"Both import attempts failed. Please make sure you have either the 'Crypto' or 'Cryptodome' library installed for the {module_name} module.")
    return module

RSA = import_crypto_module('PublicKey.RSA')
AES = import_crypto_module('Cipher.AES')
Padding = import_crypto_module('Util.Padding')

from NetworkManager import *
from GuiManager import *

class ChatApp:
    def __init__(self, my_port, second_port):
        self.my_port = my_port
        self.second_port = second_port
        self.gui_manager = GuiManager(self)
        self.gui_manager.run()

    def set_login_details(self, username_hash, password_hash):
        public_keys_dir = os.path.join('keys', 'public')
        private_keys_dir = os.path.join('keys', 'private')
        public_key_file = os.path.join(public_keys_dir, f'{username_hash}.pem')
        private_key_file = os.path.join(private_keys_dir, f'{username_hash}.pem')

        if not os.path.exists(public_key_file) or not os.path.exists(private_key_file):
            private_key, public_key = self.generate_rsa_keys()

            os.makedirs(public_keys_dir, exist_ok=True)
            os.makedirs(private_keys_dir, exist_ok=True)

            encrypted_private_key = self.encrypt_with_aes(password_hash, private_key.export_key().decode())
            with open(private_key_file, 'wb') as file:
                file.write(encrypted_private_key)

            with open(public_key_file, 'wb') as file:
                file.write(public_key.export_key())

        else:
            with open(private_key_file, 'rb') as file:
                encrypted_private_key = file.read()
            private_key = RSA.import_key(self.decrypt_with_aes(password_hash, encrypted_private_key))

            with open(public_key_file, 'rb') as file:
                public_key = RSA.import_key(file.read())

        print(private_key.export_key())
        print(public_key.export_key())

        self.network_manager = NetworkManager(my_port=self.my_port, second_port=self.second_port, buffer_size=1024, chat_app=self, prk=private_key, puk=public_key)

    def encrypt_with_aes(self, password, data):
        password = hashlib.sha256(password.encode()).digest()
        cipher = AES.new(password, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(Padding.pad(data.encode('utf-8'), AES.block_size))
        iv = cipher.iv
        return iv + ct_bytes

    def decrypt_with_aes(self, password, data):
        password = hashlib.sha256(password.encode()).digest()
        iv = data[:16]
        ct = data[16:]
        cipher = AES.new(password, AES.MODE_CBC, iv=iv)
        pt = Padding.unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode('utf-8')

    def run(self):
        self.gui_manager.run()

if __name__ == "__main__":
    my_port = int(input("What's your port: "))
    second_port = int(input("What's the second port: "))
    ca = ChatApp(my_port, second_port)
