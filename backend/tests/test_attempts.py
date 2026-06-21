import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from datetime import datetime
from main import app

FAKE_GROUP_ID = str(ObjectId())
FAKE_Q_ID = str(ObjectId())
FAKE_ATTEMPT_ID = str(ObjectId())

FAKE_QUESTION = {
    "_id": ObjectId(FAKE_Q_ID),
    "group_id": ObjectId(FAKE_GROUP_ID),
    "document_id": ObjectId(),
    "order_index": 1,
    "question_text": "What is civil rights?",
    "options": {"a": "Legal rights", "b": "Political", "c": "Social", "d": "Economic"},
    "correct_answer": "a",
    "explanation": "Civil rights are legal protections.",
    "extraction_method": "rule_based",
}

FAKE_ATTEMPT = {
    "_id": ObjectId(FAKE_ATTEMPT_ID),
    "group_id": ObjectId(FAKE_GROUP_ID),
    "document_id": ObjectId(),
    "started_at": datetime.utcnow(),
    "submitted_at": datetime.utcnow(),
    "score": 1,
    "total": 1,
    "responses": [{"question_id": ObjectId(FAKE_Q_ID), "selected": "a", "is_correct": True}],
}

@pytest.mark.asyncio
async def test_start_attempt_returns_questions(mocker):
    mock_q_col = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[FAKE_QUESTION])
    mock_q_col.find = MagicMock(return_value=mock_cursor)

    mock_att_col = AsyncMock()
    mock_att_col.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=ObjectId(FAKE_ATTEMPT_ID)))

    mock_collections = MagicMock()
    mock_collections.questions = mock_q_col
    mock_collections.attempts = mock_att_col

    mocker.patch("routers.attempts.collections", mock_collections)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/attempts", json={"group_id": FAKE_GROUP_ID})
    assert resp.status_code == 200
    data = resp.json()
    assert "attempt_id" in data
    assert len(data["questions"]) == 1
    assert "correct_answer" not in data["questions"][0]

@pytest.mark.asyncio
async def test_submit_attempt_returns_score(mocker):
    mock_q_col = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[FAKE_QUESTION])
    mock_q_col.find = MagicMock(return_value=mock_cursor)

    mock_att_col = AsyncMock()
    mock_att_col.find_one = AsyncMock(return_value={
        "_id": ObjectId(FAKE_ATTEMPT_ID),
        "group_id": ObjectId(FAKE_GROUP_ID),
        "document_id": ObjectId(),
    })
    mock_att_col.update_one = AsyncMock()

    mock_collections = MagicMock()
    mock_collections.questions = mock_q_col
    mock_collections.attempts = mock_att_col

    mocker.patch("routers.attempts.collections", mock_collections)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/attempts/{FAKE_ATTEMPT_ID}/submit",
            json={"responses": [{"question_id": FAKE_Q_ID, "selected": "a"}]}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 1
    assert data["total"] == 1
    assert data["breakdown"][0]["is_correct"] is True
