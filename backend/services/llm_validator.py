"""
Lazy, per-group LLM validation.

Role: VERIFY only — do not change correctly parsed content.
Called once per group when the user first starts a quiz for that chapter.
If the LLM call fails for any reason, the quiz proceeds with rule-based output.
"""

import json
import logging
import httpx
from bson import ObjectId
from database import collections
from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a quality checker for MCQ questions parsed from a PDF exam paper.

Your ONLY job is to VERIFY the parsed output — NOT to change it.

Rules:
1. DO NOT rewrite, rephrase, or alter question_text or any option text.
2. DO NOT invent content that is not in raw_text.
3. Examine each question in the JSON array provided. For each question, check:
   - Does question_text match what is in raw_text? (typos/truncation are OK to report)
   - Does correct_answer match the answer key in raw_text?
   - Are any required fields (question_text, options a/b/c/d, correct_answer) empty when the text IS present in raw_text?
4. Return a JSON array with one object per question, in the same order.
   - If a question looks correct: {"status": "ok"}
   - If correct_answer is wrong: {"correct_answer": "b"}  (single lowercase letter only)
   - If question_text is missing but visible in raw_text: {"question_text": "exact text from raw_text"}
   - If an option is missing but visible in raw_text: {"options": {"d": "exact text from raw_text"}}
   - If a field is missing AND cannot be found in raw_text: {"status": "ok"}  (do not invent)
5. Return ONLY valid JSON — nothing else."""


async def validate_group(group_id: str) -> bool:
    """
    Run LLM validation for all questions in a group.
    Returns True if validation ran (regardless of corrections made),
    False if validation was skipped (LLM unavailable or not configured).
    Marks the group llm_validated=True on success so it only runs once.
    """
    # Fetch questions for this group
    questions = await collections.questions.find(
        {"group_id": ObjectId(group_id)}
    ).to_list(length=500)

    if not questions:
        await _mark_validated(group_id)
        return True

    logger.info(
        "LLM validation: sending %d questions (group %s) to %s / %s",
        len(questions), group_id, settings.ollama_base_url, settings.ollama_model
    )

    # Build the payload for the LLM
    q_payload = [
        {
            "index": i,
            "question_id": str(q["_id"]),
            "question_text": q.get("question_text", ""),
            "options": q.get("options", {}),
            "correct_answer": q.get("correct_answer", ""),
            "raw_text": q.get("raw_text", ""),
        }
        for i, q in enumerate(questions)
    ]

    user_message = (
        "Validate this JSON array of parsed MCQ questions. "
        "Return a JSON array of the same length with your assessment:\n\n"
        + json.dumps(q_payload, ensure_ascii=False, indent=2)
    )

    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "format": "json",
    }

    headers = {"Content-Type": "application/json"}
    if settings.ollama_api_key:
        headers["Authorization"] = f"Bearer {settings.ollama_api_key}"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            corrections = json.loads(content)
    except Exception as e:
        logger.warning("LLM validation failed (group %s): %s — proceeding without it", group_id, e)
        await _mark_validated(group_id)
        return False

    logger.info("LLM validation succeeded for group %s", group_id)

    # Apply corrections to the DB
    if isinstance(corrections, list):
        for item in corrections:
            if not isinstance(item, dict):
                continue
            if item.get("status") == "ok":
                continue
            idx = item.get("index")
            if idx is None or idx >= len(questions):
                continue

            q = questions[idx]
            update = {}
            if "correct_answer" in item and item["correct_answer"] in "abcd":
                update["correct_answer"] = item["correct_answer"].lower()
            if "question_text" in item and item["question_text"]:
                update["question_text"] = item["question_text"]
            if "options" in item and isinstance(item["options"], dict):
                for k, v in item["options"].items():
                    if k in ("a", "b", "c", "d") and v:
                        update[f"options.{k}"] = v

            if update:
                await collections.questions.update_one(
                    {"_id": q["_id"]},
                    {"$set": update}
                )

    await _mark_validated(group_id)
    return True


async def _mark_validated(group_id: str):
    await collections.groups.update_one(
        {"_id": ObjectId(group_id)},
        {"$set": {"llm_validated": True}}
    )
