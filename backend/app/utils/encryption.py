import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from typing import Tuple, Optional
from app.core.config import settings


class PhoneEncryption:
    """
    AES-256-GCM phone number encryption utility.
    """
    
    def __init__(self, key: Optional[str] = None):
        if key is None:
            key = getattr(settings, 'AES_KEY', None) or os.environ.get('AES_KEY', '')
        
        if len(key) != 32:
            raise ValueError("AES key must be exactly 32 bytes for AES-256")
        
        self._key = key.encode('utf-8') if isinstance(key, str) else key
        self._aesgcm = AESGCM(self._key)
    
    def encrypt(self, phone: str) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypt a phone number using AES-256-GCM.
        
        Returns:
            Tuple of (ciphertext, nonce, tag)
            The ciphertext contains the encrypted phone data.
        """
        nonce = os.urandom(12)
        phone_bytes = phone.encode('utf-8')
        ciphertext = self._aesgcm.encrypt(nonce, phone_bytes, None)
        
        ciphertext_with_tag = ciphertext[:-16]
        tag = ciphertext[-16:]
        
        return ciphertext_with_tag, nonce, tag
    
    def decrypt(self, ciphertext: bytes, nonce: bytes, tag: bytes) -> str:
        """
        Decrypt a phone number.
        
        Args:
            ciphertext: The encrypted phone data (without tag)
            nonce: The 12-byte nonce used during encryption
            tag: The 16-byte authentication tag
            
        Returns:
            The decrypted phone number string
        """
        ciphertext_with_tag = ciphertext + tag
        plaintext = self._aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        return plaintext.decode('utf-8')
    
    def encrypt_to_storage(self, phone: str) -> Tuple[str, str, str]:
        """
        Encrypt phone and return base64 encoded strings for storage.
        
        Returns:
            Tuple of (encrypted_phone_b64, nonce_b64, tag_b64)
        """
        ciphertext, nonce, tag = self.encrypt(phone)
        return (
            base64.b64encode(ciphertext).decode('utf-8'),
            base64.b64encode(nonce).decode('utf-8'),
            base64.b64encode(tag).decode('utf-8')
        )
    
    def decrypt_from_storage(self, encrypted_phone_b64: str, nonce_b64: str, tag_b64: str) -> str:
        """
        Decrypt phone from base64 encoded storage values.
        """
        ciphertext = base64.b64decode(encrypted_phone_b64)
        nonce = base64.b64decode(nonce_b64)
        tag = base64.b64decode(tag_b64)
        return self.decrypt(ciphertext, nonce, tag)


phone_encryption = PhoneEncryption()
