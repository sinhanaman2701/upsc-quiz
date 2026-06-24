from datetime import datetime
from bson import ObjectId
from database import collections


async def log(document_id: str, event: str, message: str, level: str = "info", data: dict | None = None):
    await collections.logs.insert_one({
        "document_id": ObjectId(document_id),
        "event": event,
        "level": level,
        "message": message,
        "data": data or {},
        "timestamp": datetime.utcnow(),
    })
