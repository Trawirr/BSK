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
PKCS1_OAEP = import_crypto_module('Cipher.PKCS1_OAEP')
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

    def generate_aes(self, key=None, iv=None):
        if not key: 
            key = self.session_key
        if not iv: 
            iv = Random.get_random_bytes(16)
        self.aes = AES.new(key, AES.MODE_CBC, iv)
        return iv

    def encrypt_session_key(self):
        rsa_public_cipher = PKCS1_OAEP.new(RSA.import_key(self.friends_public))
        return rsa_public_cipher.encrypt(self.session_key)

    def decrypt_session_key(self, encrypted_session_key):
        rsa_private_cipher = PKCS1_OAEP.new(self.private)
        return rsa_private_cipher.decrypt(encrypted_session_key)
    
    def encrypt_message(self, message):
        iv = self.generate_aes()
        pad = AES.block_size - len(message) % AES.block_size
        message += bytes([pad]*pad)
        ciphertext = self.aes.encrypt(message)
        print("bytes pad:", bytes([pad]*pad), f"len: {len(ciphertext)}")
        encrypted_message = iv + ciphertext
        return encrypted_message

    def decrypt_message(self, ciphertext):
        if self.aes is None:
            raise ValueError("AES cipher is not initialized")

        iv = ciphertext[:16]
        ciphertext = ciphertext[16:]
        
        self.generate_aes(iv=iv)
        message = self.aes.decrypt(ciphertext)
        pad = message[-1]
        print(f"pad {pad}, len: {len(message[:-pad])}")
        return message[:-pad]
    