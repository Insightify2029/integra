# -*- coding: utf-8 -*-
"""Git Sync v3 - عمليات Git (يدوي فقط)"""

import subprocess
import time
from pathlib import Path
from typing import Callable
from datetime import datetime

from .sync_status import SyncResult

CREATE_NO_WINDOW = 0x08000000


class GitSync:
    TIMEOUT_PULL = 15
    TIMEOUT_PUSH = 15
    TIMEOUT_QUICK = 5
    
    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root
    
    def _run_git(self, args: list, timeout: int) -> tuple:
        try:
            result = subprocess.run(
                ["git"] + args, capture_output=True, text=True,
                timeout=timeout, cwd=str(self.project_root),
                creationflags=CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, "", f"انتهى الوقت ({timeout}s)"
        except FileNotFoundError:
            return False, "", "Git غير مثبت"
        except Exception as e:
            return False, "", str(e)
    
    def pull(self, on_progress: Callable[[int, str], None] = None) -> SyncResult:
        start_time = time.time()
        
        if on_progress:
            on_progress(20, "جاري جلب التحديثات...")
        
        success, stdout, stderr = self._run_git(["pull"], self.TIMEOUT_PULL)
        duration_ms = int((time.time() - start_time) * 1000)
        
        if success:
            if on_progress:
                on_progress(100, "تم جلب التحديثات")
            
            if "Already up to date" in stdout:
                message = "لا توجد تحديثات جديدة"
            else:
                message = "تم جلب التحديثات"
            
            return SyncResult(operation="git_pull", success=True,
                              message=message, duration_ms=duration_ms)
        else:
            return SyncResult(operation="git_pull", success=False,
                              message=stderr[:100] or "فشل", duration_ms=duration_ms)
    
    def push(self, commit_message: str = None,
             on_progress: Callable[[int, str], None] = None) -> SyncResult:
        start_time = time.time()
        
        if commit_message is None:
            commit_message = f"Sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        if on_progress:
            on_progress(20, "جاري إضافة الملفات...")
        self._run_git(["add", "--all"], self.TIMEOUT_QUICK)
        
        if on_progress:
            on_progress(40, "جاري حفظ التغييرات...")
        self._run_git(["commit", "-m", commit_message], self.TIMEOUT_QUICK)
        
        if on_progress:
            on_progress(60, "جاري رفع التحديثات...")
        success, stdout, stderr = self._run_git(["push"], self.TIMEOUT_PUSH)
        duration_ms = int((time.time() - start_time) * 1000)
        
        if success or "Everything up-to-date" in stderr:
            if on_progress:
                on_progress(100, "تم رفع التحديثات")
            return SyncResult(operation="git_push", success=True,
                              message="تم رفع التحديثات", duration_ms=duration_ms)
        else:
            return SyncResult(operation="git_push", success=False,
                              message=stderr[:100] or "فشل", duration_ms=duration_ms)
    
    def check_connection(self) -> bool:
        success, _, _ = self._run_git(["ls-remote", "--exit-code", "-h"], 5)
        return success
