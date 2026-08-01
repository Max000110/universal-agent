import base64
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from antigravity_cli.logging import RedactFilter


class SessionMetadata(BaseModel):
    provider: str  # "chatgpt" or "gemini"
    account_label: str = "default"
    format_type: str = "json"  # "json" or "header_string"
    imported_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_validated_at: Optional[str] = None
    is_valid: bool = False
    validation_status: str = "unvalidated"
    model_count: int = 0

    def __str__(self) -> str:
        return f"<SessionMetadata provider={self.provider} label={self.account_label} status={self.validation_status}>"


class VaultManager:
    """
    Secure local encrypted vault for session cookie storage.
    Protects secrets using Fernet (AES-128-CBC / HMAC-SHA256) derived from local key material.
    Restricts file permissions to 0600 on POSIX filesystems (Ubuntu and Termux).
    """

    def __init__(self, vault_path: Path, key_path: Path):
        self.vault_path = Path(vault_path)
        self.key_path = Path(key_path)
        self.fernet = self._init_fernet()

    def _init_fernet(self) -> Fernet:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.key_path.exists():
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as f:
                f.write(key)
            self._set_restrictive_permissions(self.key_path)
        else:
            with open(self.key_path, "rb") as f:
                key = f.read().strip()

        return Fernet(key)

    @staticmethod
    def _set_restrictive_permissions(path: Path) -> None:
        try:
            if os.name == "posix":
                os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass

    def _read_vault_file(self) -> Dict[str, Any]:
        if not self.vault_path.exists():
            return {"metadata": {}, "encrypted_secrets": {}}
        try:
            with open(self.vault_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"metadata": {}, "encrypted_secrets": {}}

    def _write_vault_file(self, data: Dict[str, Any]) -> None:
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self._set_restrictive_permissions(self.vault_path)

    def save_session(
        self,
        provider: str,
        secret_payload: Dict[str, Any],
        format_type: str,
        account_label: str = "default",
        is_valid: bool = True,
        validation_status: str = "valid",
    ) -> SessionMetadata:
        """
        Encrypts secret payload and updates metadata for a given provider.
        """
        vault_data = self._read_vault_file()

        meta = SessionMetadata(
            provider=provider,
            account_label=account_label,
            format_type=format_type,
            imported_at=datetime.now(timezone.utc).isoformat(),
            last_validated_at=datetime.now(timezone.utc).isoformat(),
            is_valid=is_valid,
            validation_status=validation_status,
        )

        secret_bytes = json.dumps(secret_payload).encode("utf-8")
        encrypted_token = self.fernet.encrypt(secret_bytes).decode("utf-8")

        vault_data["metadata"][provider] = meta.model_dump()
        vault_data["encrypted_secrets"][provider] = encrypted_token

        self._write_vault_file(vault_data)
        return meta

    def get_session_metadata(self, provider: str) -> Optional[SessionMetadata]:
        vault_data = self._read_vault_file()
        meta_dict = vault_data.get("metadata", {}).get(provider)
        if meta_dict:
            return SessionMetadata(**meta_dict)
        return None

    def get_session_secret(self, provider: str) -> Optional[Dict[str, Any]]:
        """
        Decrypts and returns secret payload for provider. Returns None if missing or corrupted.
        Secrets MUST NOT be logged or echoed.
        """
        vault_data = self._read_vault_file()
        encrypted_token = vault_data.get("encrypted_secrets", {}).get(provider)
        if not encrypted_token:
            return None
        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_token.encode("utf-8"))
            return json.loads(decrypted_bytes.decode("utf-8"))
        except Exception:
            return None

    def update_session_status(self, provider: str, is_valid: bool, status: str) -> None:
        vault_data = self._read_vault_file()
        if provider in vault_data.get("metadata", {}):
            vault_data["metadata"][provider]["is_valid"] = is_valid
            vault_data["metadata"][provider]["validation_status"] = status
            vault_data["metadata"][provider]["last_validated_at"] = datetime.now(timezone.utc).isoformat()
            self._write_vault_file(vault_data)

    def delete_session(self, provider: str) -> bool:
        vault_data = self._read_vault_file()
        removed = False
        if provider in vault_data.get("metadata", {}):
            del vault_data["metadata"][provider]
            removed = True
        if provider in vault_data.get("encrypted_secrets", {}):
            del vault_data["encrypted_secrets"][provider]
            removed = True
        if removed:
            self._write_vault_file(vault_data)
        return removed

    def list_sessions(self) -> Dict[str, SessionMetadata]:
        vault_data = self._read_vault_file()
        res = {}
        for prov, meta in vault_data.get("metadata", {}).items():
            res[prov] = SessionMetadata(**meta)
        return res
