from typing import Annotated

from loguru import logger

from fastapi import APIRouter, Depends, HTTPException, status
from slugify import slugify
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models import Category, Product, Review
from app.schemas import CreateProduct
from app.routers.auth import get_user_data_from_jwt


router = APIRouter(prefix='/reviews', tags=['reviews'])


@router.get('/')
async def all_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reviews = await db.scalars(select(Review).where(Review.is_active))
    if reviews is None:
        logger.error(f'Reviews: {reviews}')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No reviews found'
        )
    return reviews.all()

