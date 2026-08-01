import json
import re
from typing import Dict, Any, Tuple, Optional
from pydantic import BaseModel


class ValidationResult(BaseModel):
    is_valid: bool
    format_type: str  # "header_string" or "json"
    provider: str     # "chatgpt" or "gemini"
    error_message: Optional[str] = None
    account_label: str = "default"
    normalized_session: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        status = "VALID" if self.is_valid else f"INVALID ({self.error_message})"
        return f"<ValidationResult provider={self.provider} format={self.format_type} status={status}>"


class SessionValidator:
    """
    Validates imported session cookies for ChatGPT and Gemini.
    Supports both Header String format (e.g. 'key1=val1; key2=val2') and JSON format.
    Never outputs or stores unvalidated raw secrets.
    """

    CHATGPT_REQUIRED_KEYS = ["session_token", "__Secure-next-auth.session-token", "accessToken"]
    GEMINI_REQUIRED_KEYS = ["__Secure-1PSID", "__Secure-3PSID", "SID", "HSID", "SSID"]

    @classmethod
    def parse_header_string(cls, raw_str: str) -> Dict[str, str]:
        cookies = {}
        cleaned_str = raw_str.strip()
        # Strip optional "Cookie: " header prefix
        if cleaned_str.lower().startswith("cookie:"):
            cleaned_str = cleaned_str[7:].strip()

        items = cleaned_str.split(";")
        for item in items:
            if "=" in item:
                key, val = item.strip().split("=", 1)
                key = key.strip()
                val = val.strip().strip("\"'")
                if key and val:
                    cookies[key] = val
        return cookies

    @classmethod
    def parse_json_input(cls, raw_json: str) -> Dict[str, str]:
        parsed = json.loads(raw_json)
        cookies = {}
        if isinstance(parsed, dict):
            # Dict of key-value or nested format
            for k, v in parsed.items():
                if isinstance(v, str):
                    cookies[k] = v
                elif isinstance(v, dict) and "value" in v:
                    cookies[k] = str(v["value"])
        elif isinstance(parsed, list):
            # List of cookie dicts (like browser export)
            for item in parsed:
                if isinstance(item, dict) and "name" in item and "value" in item:
                    cookies[str(item["name"])] = str(item["value"])
        return cookies

    @classmethod
    def detect_format_and_parse(cls, raw_input: str) -> Tuple[str, Dict[str, str], Optional[str]]:
        raw_input = raw_input.strip()
        if not raw_input:
            return "unknown", {}, "Empty session input provided"

        # Attempt JSON parsing first
        if raw_input.startswith("{") or raw_input.startswith("["):
            try:
                cookies = cls.parse_json_input(raw_input)
                if cookies:
                    return "json", cookies, None
                return "json", {}, "JSON input contained no valid cookie key-value pairs"
            except json.JSONDecodeError as e:
                return "json", {}, f"Malformed JSON session data: {e.msg}"

        # Otherwise treat as Header String
        cookies = cls.parse_header_string(raw_input)
        if cookies:
            return "header_string", cookies, None

        return "unknown", {}, "Could not parse input as Cookie Header string or valid JSON"

    @classmethod
    def validate_session(cls, provider: str, raw_input: str, account_label: str = "default") -> ValidationResult:
        provider = provider.lower().strip()
        if provider not in ("chatgpt", "gemini"):
            return ValidationResult(
                is_valid=False,
                format_type="unknown",
                provider=provider,
                error_message=f"Unsupported provider '{provider}'. Must be 'chatgpt' or 'gemini'."
            )

        fmt_type, cookies, parse_error = cls.detect_format_and_parse(raw_input)
        if parse_error or not cookies:
            return ValidationResult(
                is_valid=False,
                format_type=fmt_type,
                provider=provider,
                error_message=parse_error or "No cookies parsed from session input",
                account_label=account_label
            )

        # Provider specific checks
        if provider == "chatgpt":
            has_chatgpt_token = any(k in cookies for k in cls.CHATGPT_REQUIRED_KEYS) or any("session" in k.lower() for k in cookies)
            if not has_chatgpt_token:
                return ValidationResult(
                    is_valid=False,
                    format_type=fmt_type,
                    provider=provider,
                    error_message="ChatGPT session missing required token (e.g. 'session_token' or '__Secure-next-auth.session-token')",
                    account_label=account_label
                )
        elif provider == "gemini":
            has_gemini_token = any(k in cookies for k in cls.GEMINI_REQUIRED_KEYS) or any("psid" in k.lower() for k in cookies)
            if not has_gemini_token:
                return ValidationResult(
                    is_valid=False,
                    format_type=fmt_type,
                    provider=provider,
                    error_message="Gemini session missing required token (e.g. '__Secure-1PSID' or '__Secure-3PSID')",
                    account_label=account_label
                )

        # Reconstruct clean cookie header string
        header_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])

        normalized_data = {
            "cookies": cookies,
            "cookie_header": header_str,
            "format_type": fmt_type,
            "cookie_count": len(cookies)
        }

        return ValidationResult(
            is_valid=True,
            format_type=fmt_type,
            provider=provider,
            account_label=account_label,
            normalized_session=normalized_data
        )
