from __future__ import annotations

from datetime import datetime
from typing import Protocol

from ..models import Programme


class SourceError(RuntimeError):
    pass


class ScheduleSource(Protocol):
    name: str

    def fetch(self, *, channel_id: str, now: datetime, days: int) -> list[Programme]: ...
