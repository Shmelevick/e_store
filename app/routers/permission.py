from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models.user import User

from .auth import get_user_data_from_jwt

router = APIRouter(prefix='/permission', tags=['permission'])


@router.patch('/')
async def switch_permission_supp_cust(
    db: Annotated[AsyncSession, Depends(get_db)],
    get_user: Annotated[dict, Depends(get_user_data_from_jwt)],
    user_id: int
):
    if not get_user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You don't have admin permission"
    )
    
    user = await db.scalar(select(User).where(User.id == user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    if user.is_supplier:
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_supplier=False, is_customer=True)
        )
        await db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'detail': 'User is a customer now, not a supplier'
        }
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(is_supplier=True, is_customer=False)
    )
    await db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'detail': 'User is a supplier now, not a customer'
    }


