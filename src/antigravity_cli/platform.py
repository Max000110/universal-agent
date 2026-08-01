import os
import sys
import shutil
from typing import Dict, Any


class PlatformEnvironment:
    """
    Detects and adapts execution environment for Termux (Android) and Ubuntu/Linux.
    Ensures safe, non-desktop, systemd-free portable operation.
    """

    @staticmethod
    def is_termux() -> bool:
        prefix = os.environ.get("PREFIX", "")
        return "com.termux" in prefix or os.path.exists("/data/data/com.termux")

    @staticmethod
    def is_ubuntu() -> bool:
        if os.path.exists("/etc/os-release"):
            try:
                with open("/etc/os-release", "r") as f:
                    content = f.read().lower()
                    return "ubuntu" in content or "debian" in content
            except Exception:
                pass
        return False

    @classmethod
    def get_platform_name(cls) -> str:
        if cls.is_termux():
            return "Termux (Android POSIX)"
        elif cls.is_ubuntu():
            return "Ubuntu Linux"
        return f"Generic {sys.platform}"

    @staticmethod
    def get_terminal_width(default_width: int = 80) -> int:
        try:
            columns = shutil.get_terminal_size((default_width, 24)).columns
            return max(columns, 40)
        except Exception:
            return default_width

    @classmethod
    def get_system_summary(cls) -> Dict[str, Any]:
        return {
            "platform": cls.get_platform_name(),
            "is_termux": cls.is_termux(),
            "is_ubuntu": cls.is_ubuntu(),
            "python_version": sys.version.split()[0],
            "terminal_width": cls.get_terminal_width(),
        }
