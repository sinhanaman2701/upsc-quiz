import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from datetime import datetime
from main import app

FAKE_DOC_ID = str(ObjectId())

FAKE_DOC = {
    "_id": ObjectId(FAKE_DOC_ID),
    "filename": "test.pdf",
    "uploaded_at": datetime.utcnow(),
    "status": "ready",
    "total_questions": 10,
    "failed_questions": 0,
}


@pytest.mark.asyncio
async def test_get_document(mocker):
    mock_col = AsyncMock()
    mock_col.find_one = AsyncMock(return_value=FAKE_DOC)

    mock_collections = MagicMock()
    mock_collections.documents = mock_col
    mocker.patch("routers.documents.collections", mock_collections)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/documents/{FAKE_DOC_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == FAKE_DOC_ID
    assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_get_document_not_found(mocker):
    mock_col = AsyncMock()
    mock_col.find_one = AsyncMock(return_value=None)

    mock_collections = MagicMock()
    mock_collections.documents = mock_col
    mocker.patch("routers.documents.collections", mock_collections)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/documents/{FAKE_DOC_ID}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_documents(mocker):
    mock_col = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[FAKE_DOC])
    mock_col.find = MagicMock(return_value=mock_cursor)

    mock_collections = MagicMock()
    mock_collections.documents = mock_col
    mocker.patch("routers.documents.collections", mock_collections)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/documents")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
