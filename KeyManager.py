from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Random import get_random_bytes

class KeyManager:
    def __init__(self) -> None:
        self.rsa_key = None

    def generate_rsa(self):
        self.rsa_key = RSA.generate(2048)

    def save_rsa(self):
        with open("private/my_private_rsa.pem", 'wb') as file:
            file.write(self.rsa_key.export_key())
            
        with open("private/my_public_rsa.pem", 'wb') as file:
            file.write(self.rsa_key.publickey().export_key())