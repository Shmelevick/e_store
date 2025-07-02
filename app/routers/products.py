from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from slugify import slugify
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models import Category, Product
from app.schemas import CreateProduct

router = APIRouter(prefix='/product', tags=['products'])

ACTIVE_STOCK = (Product.is_active) & (Product.stock > 0)


@router.get('/')
async def all_products(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    products = await db.scalars(
        select(Product)
        .where(ACTIVE_STOCK))
    if products is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There are no any products')
    return products.all()
    

@router.post('/create')
async def create_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_product: CreateProduct
):
    try:    
        await db.execute(
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
        await db.commit()
        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
            }
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Product with this slug already exists."
        )


@router.get('/{category_slug}')
async def product_by_category(
    db: Annotated[AsyncSession, Depends(get_db)],
    category_slug: str
):
    category = await db.scalar(
        select(Category).where(
            (Category.slug == category_slug) & (Category.is_active)
        )
    )
    if category is None:
        raise HTTPException(status_code=404, detail='Category not found')
    
    subcategories = await db.scalars(
        select(Category)
        .where((Category.parent_id == category.id) & Category.is_active)
    )

    cats_and_subcats_ids = [category.id] + [sub.id for sub in subcategories]

    products = await db.scalars(
        select(Product).where(
            (Product.category_id.in_(cats_and_subcats_ids))
            & ACTIVE_STOCK
        )
    )

    return products.all()


@router.get('/detail/{product_slug}')
async def product_detail(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str
):
    product = await db.scalar(
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
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str,
    new_product: CreateProduct
):
    product = await db.scalar(
        select(Product).where((Product.slug == product_slug) & ACTIVE_STOCK)
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no such product"
        )

    await db.execute(
        update(Product)
        .where(Product.slug == product_slug) & ACTIVE_STOCK
        .values(
            name=new_product.name,
            description=new_product.description,
            price=new_product.price,
            image_url=new_product.image_url,
            stock=new_product.stock,
            category_id=new_product.category
        )
    )

    await db.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product update is successful'
    }


@router.delete('/delete')
async def delete_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_id: int
):
    product = await db.scalar(
        select(Product)
        .where((Product.id == product_id) & ACTIVE_STOCK))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no such product'
        )
    await db.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(is_active=False)
    )
    await db.commit()
    
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product delete is successful'
    }