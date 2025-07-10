from datetime import datetime, timedelta
from os import getenv
from typing import Annotated

from loguru import logger

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.db_depends import get_db
from app.models.user import User
from app.schemas import CreateUser

load_dotenv()

SECRET_KEY = getenv('SECRET_KEY')
ALGORITHM = getenv('ALGORITHM')

router = APIRouter(prefix='/auth', tags=['auth'])
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def not_none(arg):
    if arg is None:
        raise Exception(f'{arg} is None!')
    return arg
    
    
async def get_user_data_from_jwt(
        token: Annotated[str, Depends(oauth2_scheme)]
    ) -> dict:
    try:
        payload = jwt.decode(
            token,
            not_none(SECRET_KEY),
            algorithms=[not_none(ALGORITHM)]
        )
        username: str = payload["sub"]
        user_id: int = payload["id"]
        is_admin: str = payload['is_admin']
        is_supplier: str = payload['is_supplier']
        is_customer: str = payload['is_customer']
        expire = payload.get('ext')

        if username is None or user_id is None:
            logger.error(f"Username: {username}, user_id: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user'
            )
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='No access token supplied (no "expire")'
            )
        if datetime.now() > datetime.fromtimestamp(expire):
            logger.error(f'Токен все. До {datetime.fromtimestamp(expire)}')
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Token is expired'
            )
        
        return {
            'username': username,
            'id': user_id,
            'is_admin': is_admin, 
            'is_supplier': is_supplier,
            'is_customer': is_customer
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate'
        )


async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str
    ):
    user = await db.scalar(select(User).where(User.username == username))
    if (
        not user 
        or not bcrypt_context.verify(password, user.hashed_password)
        or user.is_active == False
    ):
        error = f'User: {user}, verification: '
        error += f'{bcrypt_context.verify(password, user.hashed_password)}'
        logger.error(error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentical credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def create_access_token(
        username: str,
        user_id: int,
        is_admin: bool,
        is_supplier: bool,
        is_customer: bool,
        expires_delta: timedelta
):
    expire = datetime.now() + expires_delta

    encode = {
        'sub': username,
        'id': user_id,
        'is_admin': is_admin,
        'is_supplier': is_supplier,
        'is_customer': is_customer,
        'ext': expire.timestamp()
    }
    return jwt.encode(
        encode, not_none(SECRET_KEY),
        algorithm=not_none(ALGORITHM)
    )


@router.get('/read_current_user')
async def read_current_user(user: User = Depends(get_user_data_from_jwt)):
    return {"User": user}


@router.post('/token')
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user or user.is_active == False:
        logger.error(f'User: {user}')

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )
    
    token = await create_access_token(
        user.username,
        user.id,
        user.is_admin,
        user.is_supplier,
        user.is_customer,
        expires_delta=timedelta(minutes=20)
    )

    return {
        'access_token': token,
        'token_type': 'bearer'
    }


@router.post('/')
async def create_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_user: CreateUser
):
    await db.execute(
        insert(User)
        .values(
            first_name=create_user.first_name,
            last_name=create_user.last_name,
            username=create_user.username,
            email=create_user.email,
            hashed_password=bcrypt_context.hash(create_user.password)
        )
    )
    await db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transation': 'Successful'
    }


@router.delete('/delete')
async def delete_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    request_data: Annotated[dict, Depends(get_user_data_from_jwt)],
    user_id: int
):
    if request_data.get('is_admin'):
        
        user = await db.scalar(select(User).where(User.id == user_id))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'User with id {user_id} not found'
            )

        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You can't delete admin user"
            )
        
        if user.is_active:
            await db.execute(
                update(User)
                .where(User.id == user_id)
                .values(is_active=False)
            )
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is deleted'
            }
        
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=True)
        )
        await db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'detail': 'User is activated'
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You don't have admin permission"
    )
            

# @router.get('/read_current_user')
# async def read_current_user(user: User = Depends(oauth2_scheme)):
#     return user


# @router.post('/token')
# async def login(
#     db: Annotated[AsyncSession, Depends(get_db)],
#     form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
# ):
#     user = await authanticate_user(db, form_data.username, form_data.password)

#     if not user or user.is_active == False:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail='Could not validate user'
#         )

#     return {
#         'access_token': user.username,
#         'token_type': 'bearer'
#     }