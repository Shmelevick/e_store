from datetime import date

from sqlalchemy import Boolean, Float, Integer, ForeignKey, String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.backend.db import Base
from app.models import User, Product, Review


class Rating(Base):
    __tablename__ = 'ratings'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        autoincrement=True
    )
    grade: Mapped[int] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(
        ForeignKey('products.id'),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)



    

