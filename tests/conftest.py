import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.backend.db import Base
from app.backend.db_depends import get_db
from app.main import app

# Асинхронный URL для SQLite in-memory (или файл, если нужно)
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test_ecommerce.db"

# Создаём асинхронный движок
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Асинхронный sessionmaker
AsyncTestingSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)


# Создание таблиц асинхронно (выполнить один раз перед тестами)
@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        # Удаляем таблицы (если нужно)
        await conn.run_sync(Base.metadata.drop_all)
        # Создаем таблицы
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Можно по окончании сессии почистить, если нужно


# Override зависимости get_db для async сессии
async def get_db_for_tests():
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
def override_get_db():
    app.dependency_overrides[get_db] = get_db_for_tests
    yield
    app.dependency_overrides.clear()


# Фикстура для асинхронного HTTP клиента FastAPI
@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(
    transport=ASGITransport(app=app),
    base_url="http://test"
) as client:
        yield client


# Фикстура для отката транзакции после каждого теста (опционально)
@pytest_asyncio.fixture(autouse=True)
async def db_session():
    async with engine.connect() as conn:
        trans = await conn.begin()
        async_session = AsyncTestingSessionLocal(bind=conn)
        try:
            yield async_session
        finally:
            await async_session.close()
            await trans.rollback()
