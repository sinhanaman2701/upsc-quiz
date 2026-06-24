from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


def get_database() -> AsyncIOMotorDatabase:
    return get_client()[settings.db_name]


class Collections:
    @property
    def documents(self):
        return get_database()["documents"]

    @property
    def support(self):
        return get_database()["support"]

    @property
    def groups(self):
        return get_database()["groups"]

    @property
    def questions(self):
        return get_database()["questions"]

    @property
    def attempts(self):
        return get_database()["attempts"]

    @property
    def logs(self):
        return get_database()["logs"]


collections = Collections()
