import logging
import re
from typing import Any

# Regular expressions to catch secrets, cookies, bearer tokens, and JSON auth fields
REDACTION_PATTERNS = [
    (re.compile(r"(?i)(cookie\s*:\s*)([^\r\n]+)"), r"\1[REDACTED_COOKIE_HEADER]"),
    (re.compile(r"(?i)(bearer\s+)([a-zA-Z0-9\-\._~\+\/]+=*)"), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(?i)(eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)"), r"[REDACTED_JWT]"),
    (re.compile(r"(?i)(session_token|access_token|refresh_token|api_key|__Secure-next-auth\.session-token|__Secure-1PSID|__Secure-3PSID)(\"|\')?\s*[:=]\s*(\"|\')?([^\"\'\s,;}]+)(\"|\')?"), r"\1: [REDACTED_SECRET]"),
    (re.compile(r"(?i)(v1_[a-zA-Z0-9_\-]+)"), r"[REDACTED_TOKEN_PATTERN]"),
]


class RedactFilter(logging.Filter):
    """
    Logging filter that redacts sensitive values like session cookies, JWT tokens,
    and API keys from log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact_string(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: (self.redact_string(v) if isinstance(v, str) else v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.redact_string(arg) if isinstance(arg, str) else arg for arg in record.args)
        return True

    @staticmethod
    def redact_string(text: str) -> str:
        if not isinstance(text, str):
            return text
        result = text
        for pattern, replacement in REDACTION_PATTERNS:
            result = pattern.sub(replacement, result)
        return result


def setup_logger(name: str = "antigravity", level: int = logging.INFO, log_file: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    redact_filter = RedactFilter()

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(redact_filter)
    logger.addHandler(console_handler)

    # Optional File Handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)
        file_handler.addFilter(redact_filter)
        logger.addHandler(file_handler)

    return logger
