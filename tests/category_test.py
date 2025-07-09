import pytest
from fastapi import status
from loguru import logger


@pytest.mark.asyncio
async def test_create_category(async_client):
    post_response = await async_client.post(
        "/category/create",
        json={
            "name": "Test category 1",
            "parent_id": None
        }
    )
    assert post_response.status_code == status.HTTP_200_OK
    assert post_response.json() == {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }

    get_response = await async_client.get('/category/all_categories')
    assert get_response.status_code == status.HTTP_200_OK
    categories = get_response.json()

    assert any(cat['name'] == "Test category 1" for cat in categories)


@pytest.mark.asyncio
async def test_create_category_without_name_should_fail(async_client):
    post_response = await async_client.post(
        "/category/create",
        json={
            "parent_id": None
        }
    )
    assert post_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_category_with_duplicate_slug_should_fail(async_client):
    await async_client.post(
        "/category/create",
        json={
            "name": "Category A",
            "slug": "unique-slug"
        }
    )
    post_response = await async_client.post(
        "/category/create",
        json={
            "name": "Category B",
            "slug": "unique-slug"
        }
    )
    assert post_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_product(async_client):
    # Создаем категорию, чтобы привязать продукт
    category_response = await async_client.post(
        "/category/create",
        json={
            "name": "string112",
            "parent_id": None
        }
    )
    assert category_response.status_code == status.HTTP_200_OK

    # Получаем ID категории
    categories = await async_client.get("/category/all_categories")

    category_id = categories.json()[-1]['id']
    logger.warning(f'category_id={category_id}, json={categories.json}')

    # Создаем продукт
    response = await async_client.post(
        "/product/create",
        json={
            "name": "Test Product",
            "description": "Test description",
            "price": 99.99,
            "image_url": "http://example.com/image.png",
            "stock": 10,
            "category": category_id
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }

    # Проверяем, что продукт доступен
    products = await async_client.get("/product/")
    assert products.status_code == status.HTTP_200_OK
    assert any(p["name"] == "Test Product" for p in products.json())


@pytest.mark.asyncio
async def test_create_product_missing_field_should_fail(async_client):
    response = await async_client.post(
        "/product/create",
        json={
            "description": "Missing name",
            "price": 10.0,
            "image_url": "http://example.com/image.png",
            "stock": 5,
            "category": 1
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_product_duplicate_slug_should_fail(async_client):
    # Создаем категорию
    await async_client.post(
        "/category/create",
        json={"name": "Dup Category"}
    )
    categories = await async_client.get("/category/all_categories")
    category_id = categories.json()[-1]['id']

    # Создаем первый продукт
    await async_client.post(
        "/product/create",
        json={
            "name": "Dup Product",
            "description": "desc",
            "price": 1.0,
            "image_url": "http://img.com",
            "stock": 1,
            "category": category_id
        }
    )

    # Пытаемся создать второй продукт с тем же slug
    response = await async_client.post(
        "/product/create",
        json={
            "name": "Dup Product",  # slug будет тем же
            "description": "desc2",
            "price": 2.0,
            "image_url": "http://img2.com",
            "stock": 2,
            "category": category_id
        }
    )

    # Предполагаем, что будет 422, если slug уникален (если ты настроил уникальность в модели)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY