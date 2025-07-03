from pydantic import BaseModel
from typing import Optional


class CreateProduct(BaseModel):
    name: str
    description: str
    price: float
    image_url: str
    stock: int
    category_id: int
    supplier_id: Optional[int] = None


class CreateCategory(BaseModel):
    name: str
    parent_id: int | None

class CreateUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str
    