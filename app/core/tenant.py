"""Multi-tenant helpers — resolve company context from authenticated user."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Query

from app.core.models import User
from app.core import security


def get_company_id(
    current_user: User = Depends(security.get_current_user),
) -> Optional[UUID]:
    return current_user.company_id


def require_company_id(
    current_user: User = Depends(security.get_current_user),
) -> UUID:
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma startup selecionada. Use o seletor de empresa no menu.",
        )
    return current_user.company_id


def filter_by_company(query: Query, model, company_id: Optional[UUID]) -> Query:
    """Apply company_id filter when column exists and company_id is set."""
    if company_id is not None and hasattr(model, "company_id"):
        return query.filter(model.company_id == company_id)
    return query
