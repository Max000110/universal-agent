import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkspaceInfo(BaseModel):
    cwd: str
    workspace_name: str
    git_root: Optional[str] = None
    git_branch: Optional[str] = None
    is_git_repo: bool = False
    modified_files_count: int = 0


class WorkspaceManager:
    """
    Detects and manages active workspace state, Git repository details,
    current working directory, and branch metadata.
    """

    @staticmethod
    def get_workspace_info(target_dir: Optional[Path] = None) -> WorkspaceInfo:
        cwd_path = Path(target_dir or Path.cwd()).resolve()
        cwd_str = str(cwd_path)
        workspace_name = cwd_path.name or "/"

        git_root = None
        git_branch = None
        is_git_repo = False
        modified_count = 0

        # Check Git repository details
        try:
            res_root = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=cwd_str,
                capture_output=True,
                text=True,
                timeout=2
            )
            if res_root.returncode == 0:
                git_root = res_root.stdout.strip()
                is_git_repo = True
                workspace_name = Path(git_root).name

                # Get active branch
                res_branch = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=cwd_str,
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if res_branch.returncode == 0:
                    git_branch = res_branch.stdout.strip()

                # Get modified files count
                res_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=cwd_str,
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if res_status.returncode == 0 and res_status.stdout.strip():
                    modified_count = len(res_status.stdout.strip().splitlines())
        except Exception:
            pass

        return WorkspaceInfo(
            cwd=cwd_str,
            workspace_name=workspace_name,
            git_root=git_root,
            git_branch=git_branch,
            is_git_repo=is_git_repo,
            modified_files_count=modified_count
        )
