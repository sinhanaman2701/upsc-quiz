from datetime import datetime
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from database import collections
from models.schemas import StartAttemptRequest, SubmitAttemptRequest, AttemptOut, QuestionOut, OptionsOut, ExtractionMethod, BreakdownItem
from services.scoring import calculate_score

router = APIRouter()


def _serialize_question_no_answer(q: dict) -> QuestionOut:
    return QuestionOut(
        id=str(q["_id"]),
        group_id=str(q["group_id"]),
        order_index=q["order_index"],
        question_text=q["question_text"],
        options=OptionsOut(**q["options"]),
        extraction_method=ExtractionMethod(q["extraction_method"]),
    )


@router.post("/attempts")
async def start_attempt(body: StartAttemptRequest):
    questions = await collections.questions.find(
        {"group_id": ObjectId(body.group_id)}
    ).to_list(length=500)
    questions = sorted(questions, key=lambda q: q["order_index"])

    attempt_doc = {
        "group_id": ObjectId(body.group_id),
        "document_id": questions[0]["document_id"] if questions else None,
        "started_at": datetime.utcnow(),
        "submitted_at": None,
        "score": None,
        "total": len(questions),
        "responses": [],
    }
    result = await collections.attempts.insert_one(attempt_doc)

    return {
        "attempt_id": str(result.inserted_id),
        "questions": [_serialize_question_no_answer(q) for q in questions],
    }


@router.post("/attempts/{attempt_id}/submit", response_model=AttemptOut)
async def submit_attempt(attempt_id: str, body: SubmitAttemptRequest):
    attempt = await collections.attempts.find_one({"_id": ObjectId(attempt_id)})
    if not attempt:
        raise HTTPException(404, "Attempt not found")

    question_ids = [ObjectId(r.question_id) for r in body.responses]
    questions = await collections.questions.find(
        {"_id": {"$in": question_ids}}
    ).to_list(length=500)
    questions_by_id = {str(q["_id"]): q for q in questions}

    responses = [{"question_id": r.question_id, "selected": r.selected} for r in body.responses]
    score, breakdown = calculate_score(responses, questions_by_id)

    await collections.attempts.update_one(
        {"_id": ObjectId(attempt_id)},
        {"$set": {
            "submitted_at": datetime.utcnow(),
            "score": score,
            "total": len(responses),
            "responses": [
                {"question_id": ObjectId(r["question_id"]), "selected": r["selected"], "is_correct": b["is_correct"]}
                for r, b in zip(responses, breakdown)
            ],
        }}
    )

    return AttemptOut(
        id=attempt_id,
        group_id=str(attempt["group_id"]),
        score=score,
        total=len(responses),
        breakdown=[BreakdownItem(**b) for b in breakdown],
    )


@router.get("/attempts/{attempt_id}", response_model=AttemptOut)
async def get_attempt(attempt_id: str):
    attempt = await collections.attempts.find_one({"_id": ObjectId(attempt_id)})
    if not attempt:
        raise HTTPException(404, "Attempt not found")

    question_ids = [r["question_id"] for r in attempt.get("responses", [])]
    questions = await collections.questions.find(
        {"_id": {"$in": question_ids}}
    ).to_list(length=500)
    questions_by_id = {str(q["_id"]): q for q in questions}

    responses = [{"question_id": str(r["question_id"]), "selected": r["selected"]} for r in attempt["responses"]]
    _, breakdown = calculate_score(responses, questions_by_id)

    return AttemptOut(
        id=attempt_id,
        group_id=str(attempt["group_id"]),
        score=attempt["score"],
        total=attempt["total"],
        breakdown=[BreakdownItem(**b) for b in breakdown],
    )
