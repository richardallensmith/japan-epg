from __future__ import annotations

from .models import Programme


def deduplicate(programmes: list[Programme]) -> list[Programme]:
    unique: dict[tuple, Programme] = {}
    for programme in programmes:
        unique.setdefault(programme.identity(), programme)
    return sorted(unique.values(), key=lambda p: (p.start, p.stop, p.title_ja))
