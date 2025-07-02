from pydantic import BaseModel
from typing import Optional


class CreateProduct(BaseModel):
    name: str
    description: str
    price: float
    image_url: str
    stock: int
    category: int
    supplier_id: Optional[int] = None


class CreateCategory(BaseModel):
    name: str
    parent_id: int | None

