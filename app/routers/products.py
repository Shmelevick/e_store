from typing import Annotated
from datetime import date

from loguru import logger

from fastapi import APIRouter, Depends, HTTPException, status
from slugify import slugify
from sqlalchemy import insert, select, update, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models import Category, Product, Review, Rating
from app.schemas import CreateProduct, CreateReview, CreateRating
from app.routers.auth import get_user_data_from_jwt

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
    create_product: CreateProduct,
    get_user: Annotated[dict, Depends(get_user_data_from_jwt)]
):
    if get_user.get('is_supplier') or get_user.get('is_admin'):
        await db.execute(
            insert(Product).values(
                name=create_product.name,
                slug=slugify(create_product.name),
                description=create_product.description,
                price=create_product.price,
                image_url=create_product.image_url,
                stock=create_product.stock,
                category_id=create_product.category_id,
                supplier_id=create_product.supplier_id,
                rating=0.0
            )
        )
        await db.commit()
        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='You are not authorized to use this method'
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
    new_product: CreateProduct,
    get_user: Annotated[dict, Depends(get_user_data_from_jwt)]
):
    if get_user.get('is_admin') or get_user.get('is_supplier'):
        product = await db.scalar(
            select(Product).where((Product.slug == product_slug) & ACTIVE_STOCK)
        )
        
        if product is None:
            logger.error(f'''Нет продукта {Product.slug}''')
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There is no such product"
            )
        
        if get_user.get('id') != product.supplier_id:

            i = f'ID поставшика расходится. Принято {get_user.get("id")},'
            i += f'в бд {product.supplier_id}'
            logger.error(i)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to use this method"
            )

        await db.execute(
            update(Product)
            .where((Product.slug == product_slug) & ACTIVE_STOCK)
            .values(
                name=new_product.name,
                description=new_product.description,
                price=new_product.price,
                image_url=new_product.image_url,
                stock=new_product.stock,
                category_id=new_product.category_id
            )
        )

        await db.commit()

        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Product update is successful'
        }
    logger.error(f"""
Admin: {get_user.get('is_admin')}, 
is_supplier: {get_user.get('is_supplier')}
""")
    raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='You are not authorized to use this method'
)


@router.delete('/delete')
async def delete_product(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_id: int,
    get_user: Annotated[dict, Depends(get_user_data_from_jwt)]
):
    if get_user.get('is_admin') or get_user.get('is_supplier'):
        product = await db.scalar(
            select(Product)
            .where((Product.id == product_id) & ACTIVE_STOCK))
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no such product'
            )
        
        if get_user.get('id') != product.supplier_id:

            error = f'ID поставшика расходится. Принято {get_user.get("id")},'
            error += f'в бд {product.supplier_id}'
            logger.error(error)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not authorized to use this method"
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
    logger.error(f"""
Admin: {get_user.get('is_admin')}, 
is_supplier: {get_user.get('is_supplier')}
""")
    raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='You are not authorized to use this method'
)


@router.get('/detail/{product_slug}/reviews')
async def product_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str
):
    reviews = await db.scalars(
        select(CreateReview)
        .join(CreateReview.product)
        .where((Product.slug == product_slug) & (CreateReview.is_active == True))
        .options(joinedload(CreateReview.product))
    )
    if not reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reviews found"
        )
    return reviews.all()


@router.post('/detail/{product_slug}/reviews')
async def add_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str,
    get_user: Annotated[dict, Depends(get_user_data_from_jwt)],
    review: CreateReview,
    rating: CreateRating
):
    if not get_user.get('is_customer'):
        logger.error(f'User: {get_user}')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Only a customer can make reviews'
        )

    try:
        product_raw = await db.execute(
            select(Product).where(Product.slug == product_slug)
        )
        product = product_raw.scalar_one_or_none()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Product not found'
            )

        new_rating = Rating(
            grade=rating.grade,
            user_id=get_user['id'],
            product_id=product.id
        )
        db.add(new_rating)
        await db.flush()

        new_review = Review(
            user_id=get_user['id'],
            product_id=product.id,
            rating_id=new_rating.id,
            comment=review.comment,
            comment_date=date.today()
        )
        db.add(new_review)
        await db.flush()

        new_avg_rating_raw = await db.execute(
            select(func.avg(Rating.grade))
            .where(Rating.product_id == product.id, Rating.is_active == True)
        )
        new_avg_rating = new_avg_rating_raw.scalar()

        product.rating = float(round(new_avg_rating or 0, 1)) # нужен ли 'or 0'?
        db.add(product)

        await db.commit()

        return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Review and rating creation is successful'
    }
    
    except Exception as e:
        await db.rollback()
        logger.error(f'Failed to add review/rating: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to add review or rating'
        )
# customer 123456


@router.delete('detail/{product_slug}/reviews')
async def delete_reviews(
    db: Annotated[AsyncSession, Depends(get_db)],
    product_slug: str,
    get_user: Annotated[dict, Depends(get_user_data_from_jwt)]
):
    if not get_user.get('is_admin'):
        logger.error(f"""
        Admin: {get_user.get('is_admin')}, 
        user: {get_user}
    """)
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='You are not authorized to use this method'
    )

