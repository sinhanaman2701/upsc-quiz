import os
from bson import ObjectId
from database import collections
from services.parser.extractor import extract_text
from services.parser.rule_based import detect_groups, parse_questions


async def run_pipeline(pdf_path: str, document_id: str) -> dict:
    doc_filter = {"_id": ObjectId(document_id)}

    try:
        pages = extract_text(pdf_path)
    except Exception as e:
        await collections.documents.update_one(
            doc_filter,
            {"$set": {"status": "failed", "error": str(e)}}
        )
        return {"total_questions": 0, "failed_questions": 0}

    raw_groups = detect_groups(pages)
    total_questions = 0
    group_order = 0  # sequential index for groups that actually have questions

    for group_data in raw_groups:
        raw_questions = parse_questions(group_data["raw_text"])

        # Keep ALL questions the rule-based parser found; LLM validation runs lazily later
        questions_to_insert = []
        for q in raw_questions:
            questions_to_insert.append({
                "document_id": ObjectId(document_id),
                "order_index": q["order_index"],
                "question_text": q["question_text"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q.get("explanation"),
                "extraction_method": "rule_based",
                "confidence": q["confidence"],
                "raw_text": q.get("raw_text", ""),
            })

        # Skip groups that produced no questions (e.g. ToC entries)
        if not questions_to_insert:
            continue

        group_doc = {
            "document_id": ObjectId(document_id),
            "display_name": group_data["display_name"],
            "group_type": group_data["group_type"],
            "order_index": group_order,
            "question_count": len(questions_to_insert),
            "llm_validated": False,
        }
        group_result = await collections.groups.insert_one(group_doc)
        group_id = group_result.inserted_id
        group_order += 1

        # Attach group_id now that we have it
        for q in questions_to_insert:
            q["group_id"] = group_id

        await collections.questions.insert_many(questions_to_insert)
        total_questions += len(questions_to_insert)

    await collections.documents.update_one(
        doc_filter,
        {"$set": {
            "status": "ready",
            "total_questions": total_questions,
            "failed_questions": 0,
        }}
    )

    try:
        os.remove(pdf_path)
    except OSError:
        pass

    return {"total_questions": total_questions, "failed_questions": 0}
