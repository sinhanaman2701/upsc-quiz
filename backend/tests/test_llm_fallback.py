import pytest
from unittest.mock import AsyncMock, patch
from services.parser.llm_fallback import extract_with_llm

VALID_LLM_RESPONSE = """{
    "question_text": "What is the capital of India?",
    "options": {"a": "Mumbai", "b": "New Delhi", "c": "Kolkata", "d": "Chennai"},
    "correct_answer": "b",
    "explanation": "New Delhi is the capital of India."
}"""

ERROR_LLM_RESPONSE = """{"error": "no_question_found"}"""

@pytest.mark.asyncio
async def test_extract_with_llm_returns_parsed_dict(mocker):
    mock_response = AsyncMock()
    # json() is not async in httpx, so we need to set it as a regular return value
    mock_response.json = lambda: {
        "message": {"content": VALID_LLM_RESPONSE}
    }
    mock_response.raise_for_status = lambda: None

    mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response)

    result = await extract_with_llm("What is the capital of India? (a) Mumbai (b) New Delhi Answer: B")
    assert result is not None
    assert result["correct_answer"] == "b"
    assert result["options"]["a"] == "Mumbai"

@pytest.mark.asyncio
async def test_extract_with_llm_returns_none_on_error_response(mocker):
    mock_response = AsyncMock()
    # json() is not async in httpx, so we need to set it as a regular return value
    mock_response.json = lambda: {
        "message": {"content": ERROR_LLM_RESPONSE}
    }
    mock_response.raise_for_status = lambda: None

    mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response)

    result = await extract_with_llm("some garbled text with no question")
    assert result is None

@pytest.mark.asyncio
async def test_extract_with_llm_returns_none_on_network_error(mocker):
    mock_post = mocker.patch("httpx.AsyncClient.post", side_effect=Exception("connection refused"))
    result = await extract_with_llm("any text")
    assert result is None
