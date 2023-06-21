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
Random = import_crypto_module('Random')

class KeyManager:
    def __init__(self) -> None:
        self.public = None
        self.private = None
        self.friends_public = None
        self.session_key = None
        self.aes = None

    def generate_rsa(self, prk, puk):
        #self.private = RSA.generate(2048)
        #self.public = self.private.publickey()
        self.private = prk
        self.public = puk
        self.session_key = Random.get_random_bytes(32)

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