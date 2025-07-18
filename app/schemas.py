from pydantic import BaseModel, field_validator


class CreateProduct(BaseModel):
    name: str
    description: str
    price: float
    image_url: str
    stock: int
    category_id: int
    supplier_id: int

    @field_validator('name')
    def normalize_name(cls, value):
        return value.title()
    
    @field_validator('stock')
    def validate_stock(cls, value):
        if not 1000 >= value > -1:
            raise ValueError('Must be between 0 and 1000')
        return value


class CreateCategory(BaseModel):
    name: str
    parent_id: int | None = None


class CreateUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str
    

class CreateReview(BaseModel):
    comment: str

    @field_validator('comment')
    def validate_comment_length(cls, value):
        if not 10 < len(value) < 1000:
            raise ValueError('Length must be between 10 and 1000')
        return value
    
class CreateRating(BaseModel):
    grade: int

    @field_validator('grade')
    def validate_grade(cls, value):
        if not 1 <= value <= 5:
            raise ValueError('Grade must be between 1 and 5')
        return value
