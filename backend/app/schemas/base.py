"""Use: Defines request and response data shapes for shared schema helpers.
Where to use: Use this in routers and services when validating or returning shared schema helpers.
Role: Schema layer. It keeps API payloads clear and typed.
"""

from __future__ import annotations

import math
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response used by all list endpoints.

    Format:
        {
            "data": [...],
            "page": 1,
            "total": 42,
            "total_pages": 5,
            "limit": 10,
            "next": 2,
            "prev": null
        }
    """

    data: List[T]
    page: int
    total: int
    total_pages: int
    limit: int
    next: int | None
    prev: int | None

    @staticmethod
    def build(
        items: list,
        *,
        total: int,
        page: int,
        limit: int,
    ) -> "PaginatedResponse":
        total_pages = math.ceil(total / limit) if limit > 0 else 1
        next_page = page + 1 if page < total_pages else None
        prev_page = page - 1 if page > 1 else None
        return PaginatedResponse(
            data=items,
            page=page,
            total=total,
            total_pages=total_pages,
            limit=limit,
            next=next_page,
            prev=prev_page,
        )
