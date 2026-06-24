import base64
import io
from datetime import datetime

from PIL import Image

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from models.schemas import SupportTicketOut
from pymongo import ReturnDocument

from database import collections

router = APIRouter()

_MAX_DIM = 1200
_JPEG_QUALITY = 70


def _compress_image(data: bytes) -> bytes:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((_MAX_DIM, _MAX_DIM), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
    return buf.getvalue()


@router.post("/support", response_model=SupportTicketOut, response_model_by_alias=False)
async def create_support_ticket(
    message: str = Form(...),
    image: UploadFile | None = File(default=None),
):
    image_base64 = None
    image_mime = None

    if image is not None:
        if not (image.content_type or "").startswith("image/"):
            raise HTTPException(400, "Only image files are accepted")
        image_bytes = await image.read()
        if len(image_bytes) > 5 * 1024 * 1024:
            raise HTTPException(413, "Image must be under 5 MB")
        image_bytes = _compress_image(image_bytes)
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        image_mime = "image/jpeg"

    ticket = {
        "message": message,
        "image_base64": image_base64,
        "image_mime": image_mime,
        "resolved": False,
        "created_at": datetime.utcnow(),
    }
    result = await collections.support.insert_one(ticket)
    ticket["_id"] = result.inserted_id

    return ticket


@router.get("/support", response_model=list[SupportTicketOut], response_model_by_alias=False)
async def list_support_tickets():
    return await collections.support.find().sort("created_at", -1).to_list(length=500)


@router.patch("/support/{ticket_id}/resolve", response_model=SupportTicketOut, response_model_by_alias=False)
async def toggle_support_ticket_resolution(ticket_id: str):
    try:
        oid = ObjectId(ticket_id)
    except InvalidId:
        raise HTTPException(400, "Invalid ticket ID")
    ticket = await collections.support.find_one({"_id": oid})
    if not ticket:
        raise HTTPException(404, "Support ticket not found")

    updated_ticket = await collections.support.find_one_and_update(
        {"_id": oid},
        {"$set": {"resolved": not ticket.get("resolved", False)}},
        return_document=ReturnDocument.AFTER,
    )

    if not updated_ticket:
        raise HTTPException(404, "Support ticket not found")

    return updated_ticket
