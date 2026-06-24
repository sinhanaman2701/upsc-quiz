from fastapi import APIRouter, HTTPException
from bson import ObjectId
from bson.errors import InvalidId
from database import collections
from models.schemas import GroupOut, QuestionOut, OptionsOut, GroupType, ExtractionMethod

router = APIRouter()

def _serialize_group(g: dict) -> GroupOut:
    return GroupOut(
        id=str(g["_id"]),
        document_id=str(g["document_id"]),
        display_name=g["display_name"],
        group_type=GroupType(g["group_type"]),
        order_index=g["order_index"],
        question_count=g["question_count"],
    )

def _serialize_question(q: dict) -> QuestionOut:
    return QuestionOut(
        id=str(q["_id"]),
        group_id=str(q["group_id"]),
        order_index=q["order_index"],
        question_text=q["question_text"],
        options=OptionsOut(**q["options"]),
        extraction_method=ExtractionMethod(q["extraction_method"]),
    )

@router.get("/documents/{doc_id}/groups", response_model=list[GroupOut])
async def get_groups(doc_id: str):
    try:
        oid = ObjectId(doc_id)
    except InvalidId:
        raise HTTPException(400, "Invalid document ID")
    if not await collections.documents.find_one({"_id": oid}):
        raise HTTPException(404, "Document not found")
    groups = await collections.groups.find(
        {"document_id": oid}
    ).to_list(length=100)
    return [_serialize_group(g) for g in sorted(groups, key=lambda g: g["order_index"])]

@router.get("/groups/{group_id}/questions", response_model=list[QuestionOut])
async def get_questions(group_id: str):
    try:
        oid = ObjectId(group_id)
    except InvalidId:
        raise HTTPException(400, "Invalid group ID")
    if not await collections.groups.find_one({"_id": oid}):
        raise HTTPException(404, "Group not found")
    questions = await collections.questions.find(
        {"group_id": oid}
    ).to_list(length=500)
    return [_serialize_question(q) for q in sorted(questions, key=lambda q: q["order_index"])]
