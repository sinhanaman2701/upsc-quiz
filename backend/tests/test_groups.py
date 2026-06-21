import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from main import app

FAKE_DOC_ID = str(ObjectId())
FAKE_GROUP_ID = str(ObjectId())

FAKE_GROUP = {
    "_id": ObjectId(FAKE_GROUP_ID),
    "document_id": ObjectId(FAKE_DOC_ID),
    "display_name": "Chapter 1: Basic Concepts",
    "group_type": "chapter",
    "order_index": 0,
    "question_count": 5,
}

FAKE_QUESTION = {
    "_id": ObjectId(),
    "group_id": ObjectId(FAKE_GROUP_ID),
    "document_id": ObjectId(FAKE_DOC_ID),
    "order_index": 1,
    "question_text": "What is civil rights?",
    "options": {"a": "Legal rights", "b": "Political", "c": "Social", "d": "Economic"},
    "correct_answer": "a",
    "explanation": "Civil rights are...",
    "extraction_method": "rule_based",
}

@pytest.mark.asyncio
async def test_get_groups_for_document(mocker):
    mock_col = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[FAKE_GROUP])
    mock_col.find = MagicMock(return_value=mock_cursor)

    mock_collections = MagicMock()
    mock_collections.groups = mock_col
    mocker.patch("routers.groups.collections", mock_collections)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/documents/{FAKE_DOC_ID}/groups")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["display_name"] == "Chapter 1: Basic Concepts"

@pytest.mark.asyncio
async def test_get_questions_excludes_correct_answer(mocker):
    mock_col = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[FAKE_QUESTION])
    mock_col.find = MagicMock(return_value=mock_cursor)

    mock_collections = MagicMock()
    mock_collections.questions = mock_col
    mocker.patch("routers.groups.collections", mock_collections)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/groups/{FAKE_GROUP_ID}/questions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "correct_answer" not in data[0]
