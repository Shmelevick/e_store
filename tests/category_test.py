import pytest
from fastapi import status

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
