from datetime import datetime, timezone, timedelta
from bson import ObjectId
from database import collections

_IST = timezone(timedelta(hours=5, minutes=30))


async def log(document_id: str, event: str, message: str, level: str = "info", data: dict | None = None):
    await collections.logs.insert_one({
        "document_id": ObjectId(document_id),
        "event": event,
        "level": level,
        "message": message,
        "data": data or {},
        "timestamp": datetime.now(_IST).replace(tzinfo=None),
    })
