"""
crypto.py — Cifrado AES-256 para /knowledge y /database
Protege los documentos sensibles en caso de pérdida de la USB.
Usa AES-256-GCM (autenticado) via la librería `cryptography`.
"""

import os
import json
import logging
import getpass
import hashlib
from pathlib import Path
from typing import Optional

log = logging.getLogger("crypto")

ENCRYPTED_EXT = ".enc"
SALT_FILE     = ".salt"    # salt guardado junto a la clave derivada


def _derive_key(password: str, salt: bytes) -> bytes:
    """Deriva una clave AES-256 desde la contraseña usando PBKDF2."""
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,  # NIST 2023 recommendation
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_file(path: Path, key: bytes) -> Path:
    """
    Cifra un archivo con AES-256-GCM.
    Guarda el resultado en <nombre>.enc y elimina el original.
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    data  = path.read_bytes()
    nonce = os.urandom(12)  # 96 bits para GCM
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    out_path = path.with_suffix(path.suffix + ENCRYPTED_EXT)
    out_path.write_bytes(nonce + ciphertext)
    path.unlink()
    return out_path


def decrypt_file(path: Path, key: bytes) -> Path:
    """
    Descifra un archivo .enc con AES-256-GCM.
    Restaura el archivo original y elimina el .enc.
    """
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    raw    = path.read_bytes()
    nonce  = raw[:12]
    ciphertext = raw[12:]
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        raise ValueError("Contraseña incorrecta o archivo dañado.")

    out_path = path.with_suffix("")  # elimina .enc
    out_path.write_bytes(plaintext)
    path.unlink()
    return out_path


def encrypt_directory(directory: Path, key: bytes,
                       extensions: tuple = (".pdf", ".txt", ".md", ".docx",
                                            ".json", ".npy")):
    """Cifra todos los archivos de un directorio con las extensiones dadas."""
    count = 0
    for f in directory.rglob("*"):
        if f.is_file() and f.suffix in extensions and not f.name.endswith(ENCRYPTED_EXT):
            encrypt_file(f, key)
            count += 1
    log.info(f"Cifrados {count} archivos en {directory.name}")


def decrypt_directory(directory: Path, key: bytes):
    """Descifra todos los archivos .enc de un directorio."""
    count = 0
    for f in directory.rglob(f"*{ENCRYPTED_EXT}"):
        decrypt_file(f, key)
        count += 1
    log.info(f"Descifrados {count} archivos en {directory.name}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI de cifrado
# ─────────────────────────────────────────────────────────────────────────────

class CryptoManager:
    """
    Gestiona el ciclo de vida del cifrado para Pocket Mentor EDU.
    Guarda el salt en la raíz del proyecto para permitir re-derivar la clave.
    """

    def __init__(self, base_dir: Path):
        self.base_dir  = base_dir
        self.salt_path = base_dir / SALT_FILE
        self._key: Optional[bytes] = None

    def _get_or_create_salt(self) -> bytes:
        if self.salt_path.exists():
            return self.salt_path.read_bytes()
        salt = os.urandom(32)
        self.salt_path.write_bytes(salt)
        return salt

    def unlock(self, password: str) -> bool:
        """
        Deriva la clave desde la contraseña.
        Retorna True si el proceso fue exitoso (no valida contra datos cifrados).
        """
        salt = self._get_or_create_salt()
        self._key = _derive_key(password, salt)
        log.info("Clave derivada correctamente.")
        return True

    def lock(self, encrypt_knowledge: bool = True, encrypt_database: bool = True):
        """Cifra /knowledge y /database."""
        if not self._key:
            raise RuntimeError("Llama a unlock() primero.")
        if encrypt_knowledge:
            encrypt_directory(self.base_dir / "knowledge", self._key)
        if encrypt_database:
            encrypt_directory(self.base_dir / "database",  self._key,
                               extensions=(".json", ".npy"))

    def unlock_data(self, decrypt_knowledge: bool = True,
                    decrypt_database: bool = True):
        """Descifra /knowledge y /database."""
        if not self._key:
            raise RuntimeError("Llama a unlock() primero.")
        if decrypt_knowledge:
            decrypt_directory(self.base_dir / "knowledge", self._key)
        if decrypt_database:
            decrypt_directory(self.base_dir / "database",  self._key)

    @property
    def is_unlocked(self) -> bool:
        return self._key is not None

    def prompt_password(self) -> bool:
        """Solicita contraseña por consola de forma segura."""
        try:
            pwd = getpass.getpass("🔐 Contraseña de Pocket Mentor EDU: ")
            if not pwd:
                log.warning("Sin contraseña. Los datos cifrados no estarán disponibles.")
                return False
            return self.unlock(pwd)
        except (KeyboardInterrupt, EOFError):
            return False
