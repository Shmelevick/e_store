from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(
    'postgresql+asyncpg://ecommerce:ecommerce@localhost:5432/ecommerce_db',
    echo=True
)
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


class Base(DeclarativeBase):
    pass


# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, DeclarativeBase


# engine = create_engine('sqlite:///ecommerce.db', echo=True)
# SessionLocal = sessionmaker(bind=engine)


# class Base(DeclarativeBase):
#     pass





