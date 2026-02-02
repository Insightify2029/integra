# -*- coding: utf-8 -*-
"""Sync Status v3 - حالة المزامنة الموحدة"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


class SyncState(Enum):
    IDLE = "idle"
    SYNCING = "syncing"
    SUCCESS = "success"
    ERROR = "error"
    OFFLINE = "offline"
    PARTIAL = "partial"


@dataclass
class SyncResult:
    operation: str
    success: bool
    message: str
    duration_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SyncStatus:
    state: SyncState = SyncState.IDLE
    current_operation: str = ""
    progress_percent: int = 0
    progress_message: str = ""
    results: List[SyncResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    @property
    def is_syncing(self) -> bool:
        return self.state == SyncState.SYNCING
    
    @property
    def total_duration_ms(self) -> int:
        if self.started_at and self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds() * 1000)
        return 0
    
    @property
    def all_success(self) -> bool:
        return all(r.success for r in self.results)
    
    @property
    def has_errors(self) -> bool:
        return any(not r.success for r in self.results)
    
    def add_result(self, operation: str, success: bool, message: str, duration_ms: int = 0):
        self.results.append(SyncResult(operation=operation, success=success,
                                        message=message, duration_ms=duration_ms))
    
    def start(self):
        self.state = SyncState.SYNCING
        self.started_at = datetime.now()
        self.results = []
        self.progress_percent = 0
    
    def finish(self):
        self.finished_at = datetime.now()
        if not self.results:
            self.state = SyncState.IDLE
        elif self.all_success:
            self.state = SyncState.SUCCESS
        elif self.has_errors and any(r.success for r in self.results):
            self.state = SyncState.PARTIAL
        else:
            self.state = SyncState.ERROR
        self.progress_percent = 100
    
    def get_summary(self) -> str:
        if self.state == SyncState.SUCCESS:
            return f"تمت المزامنة ({self.total_duration_ms}ms)"
        elif self.state == SyncState.PARTIAL:
            errors = [r for r in self.results if not r.success]
            return f"اكتملت جزئياً ({len(errors)} أخطاء)"
        elif self.state == SyncState.ERROR:
            return "فشلت المزامنة"
        elif self.state == SyncState.OFFLINE:
            return "لا يوجد اتصال"
        return ""
