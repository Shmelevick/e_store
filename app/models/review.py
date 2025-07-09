from datetime import date

from sqlalchemy import Boolean, Float, Integer, ForeignKey, String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.backend.db import Base


class Review(Base):
    __tablename__ = 'reviews'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(
        ForeignKey('products.id'),
        nullable=False
    )
    rating_id: Mapped[int] = mapped_column(
        ForeignKey('ratings.id')
    )
    comment: Mapped[str] = mapped_column(String, nullable=False)
    comment_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        nullable=False
    )
    rating: Mapped['Rating'] = relationship('Rating', back_populates='review')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
