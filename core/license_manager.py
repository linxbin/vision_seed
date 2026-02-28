import base64
import hashlib
import hmac
import json
import os
import platform
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from core.app_paths import get_user_license_dir


class LicenseManager:
    """本地授权管理（交易层）：设备绑定 + 授权码校验 + 本地授权文件。"""

    TOKEN_PREFIX = "VS1"
    LOCAL_SCHEMA_VERSION = 1
    # V1 使用 HMAC 实现最小可落地的本地验签。
    # 注意：客户端内置密钥属于“提高门槛”，不等同强对抗安全。
    _SIGNING_SECRET = "visionseed-license-v1::change-this-before-release"

    def __init__(self):
        self.license_dir = get_user_license_dir()
        self.license_file = os.path.join(self.license_dir, "license.json")

    @staticmethod
    def _b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

    @staticmethod
    def _b64url_decode(data: str) -> bytes:
        padding = "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode((data + padding).encode("ascii"))

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _safe_parse_utc(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            normalized = value.replace("Z", "+00:00")
            dt = datetime.fromisoformat(normalized)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            return None

    @staticmethod
    def _stable_json(payload: Dict[str, Any]) -> bytes:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    @classmethod
    def _sign_payload(cls, payload: Dict[str, Any]) -> str:
        digest = hmac.new(
            cls._SIGNING_SECRET.encode("utf-8"),
            cls._stable_json(payload),
            hashlib.sha256,
        ).digest()
        return cls._b64url_encode(digest)

    @classmethod
    def _verify_signature(cls, payload: Dict[str, Any], signature: str) -> bool:
        expected = cls._sign_payload(payload)
        return hmac.compare_digest(expected, signature)

    @classmethod
    def create_activation_token(
        cls,
        license_id: str,
        order_ref: str,
        device_hash: str,
        expires_at: Optional[str] = None,
    ) -> str:
        payload = {
            "license_id": license_id,
            "order_ref": order_ref,
            "device_hash": device_hash,
            "issued_at": cls._utc_now_iso(),
            "expires_at": expires_at,
            "status": "active",
            "schema_version": cls.LOCAL_SCHEMA_VERSION,
        }
        payload_b64 = cls._b64url_encode(cls._stable_json(payload))
        signature = cls._sign_payload(payload)
        return f"{cls.TOKEN_PREFIX}.{payload_b64}.{signature}"

    def get_device_hash(self) -> str:
        machine_data = {
            "node": platform.node(),
            "system": platform.system(),
            "release": platform.release(),
            "processor": platform.processor(),
            "mac": str(uuid.getnode()),
            "arch": platform.machine(),
        }
        raw = self._stable_json(machine_data)
        return "sha256:" + hashlib.sha256(raw).hexdigest()

    def get_device_code(self) -> str:
        device_hash = self.get_device_hash()
        return device_hash.replace("sha256:", "")[:16].upper()

    def _decode_token(self, token: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        token = (token or "").strip()
        parts = token.split(".")
        if len(parts) != 3:
            return False, "Invalid token format.", None

        prefix, payload_b64, signature = parts
        if prefix != self.TOKEN_PREFIX:
            return False, "Invalid token prefix.", None

        try:
            payload_raw = self._b64url_decode(payload_b64)
            payload = json.loads(payload_raw.decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return False, "Invalid token payload.", None

        if not isinstance(payload, dict):
            return False, "Invalid token payload type.", None

        if not self._verify_signature(payload, signature):
            return False, "Token signature verification failed.", None

        return True, "ok", payload

    def validate_token_for_current_device(self, token: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        ok, message, payload = self._decode_token(token)
        if not ok or payload is None:
            return False, message, None

        if payload.get("status") != "active":
            return False, "License is not active.", None

        if payload.get("schema_version") != self.LOCAL_SCHEMA_VERSION:
            return False, "Unsupported license schema version.", None

        token_device_hash = payload.get("device_hash")
        current_device_hash = self.get_device_hash()
        if token_device_hash != current_device_hash:
            return False, "License device mismatch.", None

        expires_at = self._safe_parse_utc(payload.get("expires_at"))
        if expires_at and expires_at < datetime.now(timezone.utc):
            return False, "License has expired.", None

        return True, "ok", payload

    def activate_with_token(self, token: str) -> Tuple[bool, str]:
        ok, message, payload = self.validate_token_for_current_device(token)
        if not ok or payload is None:
            return False, message

        local_data = {
            "schema_version": self.LOCAL_SCHEMA_VERSION,
            "activated_at": self._utc_now_iso(),
            "token": token.strip(),
            "license_id": payload.get("license_id", ""),
            "order_ref_masked": str(payload.get("order_ref", ""))[-6:],
        }

        try:
            with open(self.license_file, "w", encoding="utf-8") as f:
                json.dump(local_data, f, ensure_ascii=False, indent=2)
            return True, "License activated."
        except OSError as e:
            return False, f"Failed to write license file: {e}"

    def clear_local_license(self) -> bool:
        try:
            if os.path.exists(self.license_file):
                os.remove(self.license_file)
            return True
        except OSError:
            return False

    def check_local_license(self) -> Tuple[bool, str]:
        if not os.path.exists(self.license_file):
            return False, "License file not found."

        try:
            with open(self.license_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return False, "License file is unreadable."

        token = data.get("token", "")
        ok, message, _payload = self.validate_token_for_current_device(token)
        return ok, message

    def get_local_license_summary(self) -> Dict[str, str]:
        if not os.path.exists(self.license_file):
            return {"licensed": "false"}
        try:
            with open(self.license_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "licensed": "true",
                "license_id": str(data.get("license_id", "")),
                "order_ref_masked": str(data.get("order_ref_masked", "")),
                "activated_at": str(data.get("activated_at", "")),
            }
        except (OSError, json.JSONDecodeError):
            return {"licensed": "false"}
