"""Internal utilities."""
from __future__ import annotations

from datetime import datetime
from typing import Optional


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 datetime string, handling Z suffix for Python 3.9+."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
