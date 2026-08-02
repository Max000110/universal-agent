import os
from typing import Dict, Optional
from pydantic import BaseModel, Field


class PermissionRequest(BaseModel):
    action_type: str  # "shell_execution", "filesystem_write", "network_access"
    target: str
    reason: str


class PermissionDecision(BaseModel):
    allowed: bool
    mode: str  # "allow_once", "allow_session", "deny"


class PermissionManager:
    """
    Permission framework for sensitive agentic operations (shell execution,
    filesystem writes, network requests). Supports session memory and policy configuration.
    """

    def __init__(self, mode: str = "ask"):
        self.mode = mode  # "ask", "allow_all", "deny_all"
        self.session_permissions: Dict[str, bool] = {}

    def set_mode(self, mode: str) -> None:
        if mode in ("ask", "allow_all", "deny_all"):
            self.mode = mode

    def is_permission_granted(self, request: PermissionRequest) -> Optional[bool]:
        if self.mode == "allow_all":
            return True
        if self.mode == "deny_all":
            return False

        key = f"{request.action_type}:{request.target}"
        if key in self.session_permissions:
            return self.session_permissions[key]

        return None  # Prompt user

    def grant_permission(self, request: PermissionRequest, decision_mode: str) -> bool:
        key = f"{request.action_type}:{request.target}"
        if decision_mode == "allow_session":
            self.session_permissions[key] = True
            return True
        elif decision_mode == "allow_once":
            return True
        else:
            self.session_permissions[key] = False
            return False
