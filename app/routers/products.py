from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.backend.db_depends import get_db
from typing import Annotated

from app.models import *
from sqlalchemy import insert, select, update
from app.schemas import CreateProduct

from slugify import slugify

from loguru import logger

router = APIRouter(prefix='/product', tags=['products'])

ACTIVE_STOCK = (Product.is_active == True) & (Product.stock > 0)

@router.get('/')
async def all_products(
    db: Annotated[Session, Depends(get_db)],
):
    products = db.scalars(
        select(Product)
        .where(ACTIVE_STOCK)).all()
    if products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no any products')
    return products
    

@router.post('/create')
async def create_product(
    db: Annotated[Session, Depends(get_db)],
    create_product: CreateProduct
):
    db.execute(
        insert(Product)
        .values(
            name=create_product.name,
            slug=slugify(create_product.name),
            description=create_product.description,
            price=create_product.price,
            image_url=create_product.image_url,
            stock=create_product.stock,
            category_id=create_product.category,
            rating=0.0
        )
    )
    db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
        }


@router.get('/{category_slug}')
async def product_by_category(
    db: Annotated[Session, Depends(get_db)],
    category_slug: str
):
    category = db.scalar(
        select(Category).where(
            (Category.slug == category_slug) & (Category.is_active == True)
        )
    )
    if category is None:
        raise HTTPException(status_code=404, detail='Category not found')
    
    subcategories = db.scalars(
        select(Category)
        .where((Category.parent_id == category.id) & Category.is_active == True)
    ).all()

    category_ids = [category.id] + [sub.id for sub in subcategories]

    products = db.scalars(
        select(Product).where(
            (Product.category_id.in_(category_ids))
            & ACTIVE_STOCK
        )
    ).all()

    return products



@router.get('/detail/{product_slug}')
async def product_detail(
    db: Annotated[Session, Depends(get_db)],
    product_slug: str
):
    product = db.scalar(
        select(Product).where((Product.slug == product_slug) & ACTIVE_STOCK)
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no any product"
        )
    return product


@router.put('/detail/{product_slug}')
async def update_product(
    db: Annotated[Session, Depends(get_db)],
    product_slug: str,
    new_product: CreateProduct
):
    product = db.scalar(
        select(Product).where((Product.slug == product_slug) & ACTIVE_STOCK)
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no such product"
        )

    db.execute(
        update(Product)
        .where(Product.slug == product_slug) & ACTIVE_STOCK
        .values(
            name = new_product.name,
            description = new_product.description,
            price = new_product.price,
            image_url = new_product.image_url,
            stock = new_product.stock,
            category_id = new_product.category
        )
    )

    db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product update is successful'
    }




@router.delete('/delete')
async def delete_product(
    db: Annotated[Session, Depends(get_db)],
    product_id: int
):
    product = db.scalar(
        select(Product)
        .where((Product.id == product_id) & ACTIVE_STOCK))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no such product'
        )
    db.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(is_active=False)
    )
    db.commit()
    
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product delete is successful'
    }