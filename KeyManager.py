from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from Cryptodome.Random import get_random_bytes

class KeyManager:
    def __init__(self) -> None:
        self.public = None
        self.private = None
        self.friends_public = None
        self.session_key = None
        self.aes = None

    def generate_rsa(self):
        self.private = RSA.generate(2048)
        self.public = self.private.publickey()
        self.session_key = get_random_bytes(32)

    def save_rsa(self):
        with open("private/my_private_rsa.pem", 'wb') as file:
            file.write(self.private.export_key())
            
        with open("public/my_public_rsa.pem", 'wb') as file:
            file.write(self.public.export_key())

    def generate_aes(self, key=None):
        if not key: key = self.session_key
        nonce = b"1010101011010111"
        self.aes = AES.new(key, AES.MODE_EAX, nonce)
        print(f"AES created: {self.aes}")

    def encrypt_session_key(self):
        pass