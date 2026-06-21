import os
import shutil
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from bson import ObjectId
from database import collections
from models.schemas import DocumentOut, DocumentStatus
from services.parser.pipeline import run_pipeline
from config import settings

router = APIRouter()


def _serialize_doc(doc: dict) -> DocumentOut:
    return DocumentOut(
        id=str(doc["_id"]),
        filename=doc["filename"],
        uploaded_at=doc["uploaded_at"],
        status=doc["status"],
        total_questions=doc.get("total_questions", 0),
        failed_questions=doc.get("failed_questions", 0),
    )


@router.post("/documents/upload", response_model=DocumentOut)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    os.makedirs(settings.upload_dir, exist_ok=True)
    safe_name = os.path.basename(file.filename)
    save_path = os.path.join(settings.upload_dir, f"{ObjectId()}_{safe_name}")

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = {
        "filename": file.filename,
        "uploaded_at": datetime.utcnow(),
        "status": "processing",
        "total_questions": 0,
        "failed_questions": 0,
    }
    result = await collections.documents.insert_one(doc)
    doc["_id"] = result.inserted_id

    background_tasks.add_task(run_pipeline, save_path, str(result.inserted_id))
    return _serialize_doc(doc)


@router.get("/documents", response_model=list[DocumentOut])
async def list_documents():
    docs = await collections.documents.find().to_list(length=100)
    return [_serialize_doc(d) for d in docs]


@router.get("/documents/{doc_id}", response_model=DocumentOut)
async def get_document(doc_id: str):
    doc = await collections.documents.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(404, "Document not found")
    return _serialize_doc(doc)
