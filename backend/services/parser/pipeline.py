import os
import traceback
from bson import ObjectId
from database import collections
from services.parser.extractor import extract_text
from services.parser.rule_based import detect_groups, parse_questions
from services.upload_logger import log as upload_log


async def run_pipeline(pdf_path: str, document_id: str) -> dict:
    doc_filter = {"_id": ObjectId(document_id)}

    await upload_log(document_id, "pipeline_started", "PDF text extraction started")

    try:
        pages = extract_text(pdf_path)
    except Exception as e:
        await upload_log(document_id, "extraction_failed",
                         f"Text extraction failed: {e}", level="error",
                         data={"error": str(e), "traceback": traceback.format_exc()})
        await collections.documents.update_one(
            doc_filter,
            {"$set": {"status": "failed", "error": str(e)}}
        )
        return {"total_questions": 0, "failed_questions": 0}

    await upload_log(document_id, "extraction_complete",
                     f"Text extracted from {len(pages)} pages",
                     data={"page_count": len(pages)})

    try:
        raw_groups = detect_groups(pages)
        await upload_log(document_id, "groups_detected",
                         f"{len(raw_groups)} group(s) detected",
                         data={"group_count": len(raw_groups),
                               "groups": [g["display_name"] for g in raw_groups]})

        total_questions = 0
        group_order = 0

        for group_data in raw_groups:
            raw_questions = parse_questions(group_data["raw_text"])

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

            if not questions_to_insert:
                await upload_log(document_id, "group_skipped",
                                 f"Skipped '{group_data['display_name']}' — no questions parsed",
                                 data={"group_name": group_data["display_name"]})
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

            for q in questions_to_insert:
                q["group_id"] = group_id

            await collections.questions.insert_many(questions_to_insert)
            total_questions += len(questions_to_insert)

            await upload_log(document_id, "group_parsed",
                             f"'{group_data['display_name']}' — {len(questions_to_insert)} questions",
                             data={"group_name": group_data["display_name"],
                                   "question_count": len(questions_to_insert)})

    except Exception as e:
        await upload_log(document_id, "pipeline_failed",
                         f"Pipeline error: {e}", level="error",
                         data={"error": str(e), "traceback": traceback.format_exc()})
        await collections.documents.update_one(
            doc_filter,
            {"$set": {"status": "failed", "error": str(e)}}
        )
        return {"total_questions": 0, "failed_questions": 0}

    await collections.documents.update_one(
        doc_filter,
        {"$set": {
            "status": "ready",
            "total_questions": total_questions,
            "failed_questions": 0,
        }}
    )

    await upload_log(document_id, "pipeline_complete",
                     f"Parsing complete — {total_questions} questions across {group_order} groups",
                     data={"total_questions": total_questions, "group_count": group_order})

    try:
        os.remove(pdf_path)
    except OSError:
        pass

    return {"total_questions": total_questions, "failed_questions": 0}
