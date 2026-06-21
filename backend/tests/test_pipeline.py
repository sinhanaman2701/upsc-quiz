import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from services.parser.pipeline import run_pipeline

MOCK_PAGES = [(1, """CHAPTER – 1 TEST CHAPTER
1. What is X?
(a) Option A
(b) Option B
(c) Option C
(d) Option D
1. Answer: A
Explanation: X is option A.

2. Garbled question without answer
(a) A
(b) B
""")]


def _insert_one_factory(store=None):
    """Return an AsyncMock for insert_one that returns a result with inserted_id."""
    inserted_id = ObjectId()

    async def _insert_one(doc):
        if store is not None:
            store.append(doc)
        result = MagicMock()
        result.inserted_id = inserted_id
        return result

    return AsyncMock(side_effect=_insert_one)


def _make_mock_collections(doc_updates, inserted_groups=None, inserted_questions=None):
    mock_col = MagicMock()

    mock_groups_col = AsyncMock()
    mock_groups_col.insert_one = _insert_one_factory(inserted_groups)
    mock_groups_col.update_one = AsyncMock()

    mock_questions_col = AsyncMock()
    if inserted_questions is not None:
        async def _insert_many(qs):
            inserted_questions.extend(qs)
        mock_questions_col.insert_many = AsyncMock(side_effect=_insert_many)
    else:
        mock_questions_col.insert_many = AsyncMock()

    mock_docs_col = AsyncMock()
    async def _update_one(f, u):
        doc_updates.append(u)
    mock_docs_col.update_one = AsyncMock(side_effect=_update_one)

    mock_col.groups = mock_groups_col
    mock_col.questions = mock_questions_col
    mock_col.documents = mock_docs_col

    return mock_col


@pytest.mark.asyncio
async def test_pipeline_writes_groups_and_questions(mocker):
    mocker.patch("services.parser.pipeline.extract_text", return_value=MOCK_PAGES)
    mocker.patch("services.parser.pipeline.extract_with_llm", return_value=None)

    inserted_groups = []
    inserted_questions = []
    doc_updates = []

    mock_col = _make_mock_collections(doc_updates, inserted_groups, inserted_questions)
    mocker.patch("services.parser.pipeline.collections", mock_col)

    result = await run_pipeline("/fake/path.pdf", str(ObjectId()))
    assert "total_questions" in result
    assert result["total_questions"] >= 1


@pytest.mark.asyncio
async def test_pipeline_marks_document_ready_on_success(mocker):
    mocker.patch("services.parser.pipeline.extract_text", return_value=MOCK_PAGES)
    mocker.patch("services.parser.pipeline.extract_with_llm", return_value=None)

    doc_updates = []
    mock_col = _make_mock_collections(doc_updates)
    mocker.patch("services.parser.pipeline.collections", mock_col)

    await run_pipeline("/fake/path.pdf", str(ObjectId()))
    final_update = doc_updates[-1]
    assert final_update["$set"]["status"] == "ready"


@pytest.mark.asyncio
async def test_pipeline_marks_document_failed_on_extract_error(mocker):
    mocker.patch("services.parser.pipeline.extract_text", side_effect=FileNotFoundError("not found"))

    doc_updates = []
    mock_docs_col = AsyncMock()
    async def _update_one(f, u):
        doc_updates.append(u)
    mock_docs_col.update_one = AsyncMock(side_effect=_update_one)

    mock_col = MagicMock()
    mock_col.documents = mock_docs_col
    mocker.patch("services.parser.pipeline.collections", mock_col)

    await run_pipeline("/nonexistent.pdf", str(ObjectId()))
    assert doc_updates[-1]["$set"]["status"] == "failed"
