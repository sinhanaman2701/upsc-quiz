import os
from datetime import datetime
from bson import ObjectId
from database import collections
from services.parser.extractor import extract_text
from services.parser.rule_based import detect_groups, parse_questions
from services.parser.llm_fallback import extract_with_llm


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
    failed_questions = 0

    for group_data in raw_groups:
        group_doc = {
            "document_id": ObjectId(document_id),
            "display_name": group_data["display_name"],
            "group_type": group_data["group_type"],
            "order_index": group_data["order_index"],
            "question_count": 0,
        }
        group_result = await collections.groups.insert_one(group_doc)
        group_id = group_result.inserted_id

        raw_questions = parse_questions(group_data["raw_text"])
        questions_to_insert = []

        for q in raw_questions:
            if q["confidence"] < 1.0:
                # LLM fallback for low-confidence questions
                llm_result = await extract_with_llm(
                    f"Question {q['order_index']}.\n{q['question_text']}"
                )
                if llm_result:
                    q.update(llm_result)
                    q["extraction_method"] = "llm"
                else:
                    failed_questions += 1
                    continue
            else:
                q["extraction_method"] = "rule_based"

            # Final validation
            if not (q.get("question_text") and q.get("correct_answer") and
                    q.get("options", {}).get("a")):
                failed_questions += 1
                continue

            questions_to_insert.append({
                "group_id": group_id,
                "document_id": ObjectId(document_id),
                "order_index": q["order_index"],
                "question_text": q["question_text"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q.get("explanation"),
                "extraction_method": q["extraction_method"],
            })

        if questions_to_insert:
            await collections.questions.insert_many(questions_to_insert)
            total_questions += len(questions_to_insert)

        await collections.groups.update_one(
            {"_id": group_id},
            {"$set": {"question_count": len(questions_to_insert)}}
        )

    await collections.documents.update_one(
        doc_filter,
        {"$set": {
            "status": "ready",
            "total_questions": total_questions,
            "failed_questions": failed_questions,
        }}
    )

    # Clean up uploaded file (best-effort)
    try:
        os.remove(pdf_path)
    except OSError:
        pass

    return {"total_questions": total_questions, "failed_questions": failed_questions}
