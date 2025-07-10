from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.backend.db import Base
from app.models import Category


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float)
    image_url: Mapped[str] = mapped_column(String)
    stock: Mapped[int] = mapped_column(Integer)
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'),
        nullable=True
    )
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    rating: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category: Mapped['Category'] = relationship(
        'Category', back_populates='products'
    )