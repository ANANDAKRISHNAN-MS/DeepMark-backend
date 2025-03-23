from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken

from models import security

class Encrypt:
    master_key = security.master.master_key
    master_cipher = Fernet(master_key)

    @staticmethod
    async def encrypt_user_key(user_key: bytes) -> str:
        """Encrypts a user key and returns it as a UTF-8 string for storage."""
        return Encrypt.master_cipher.encrypt(user_key).decode("utf-8") 

    @staticmethod
    async def generate_user_key() -> str:
        """Generates and encrypts a user key, returning it as a UTF-8 string."""
        user_key = Fernet.generate_key()
        return await Encrypt.encrypt_user_key(user_key)

    @staticmethod
    async def encrypt_data(sensitive_data: str, user_cipher: Fernet) -> str:
        """Encrypts user data and returns it as a UTF-8 string."""
        if not isinstance(user_cipher, Fernet):
            raise ValueError("Invalid user cipher provided.")
        return user_cipher.encrypt(sensitive_data.encode()).decode("utf-8")  # Convert to string


class Decrypt:
    master_cipher = Encrypt.master_cipher

    @staticmethod
    async def decrypt_user_key(encrypted_user_key: str) -> bytes:
        """Decrypts a user key stored as a string and returns bytes."""
        return Decrypt.master_cipher.decrypt(encrypted_user_key.encode("utf-8"))

    @staticmethod
    async def generate_user_cipher(encrypted_user_key: str) -> Fernet:
        """Generates a Fernet cipher using a decrypted user key."""
        decrypted_user_key = await Decrypt.decrypt_user_key(encrypted_user_key)
        return Fernet(decrypted_user_key)

    @staticmethod
    async def decrypt_data(encrypted_data: str, user_cipher: Fernet) -> str:
        """Decrypts user data stored as a UTF-8 string."""
        try:
            if not isinstance(user_cipher, Fernet):
                raise ValueError("Invalid user cipher provided.")
            return user_cipher.decrypt(encrypted_data.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            return None

