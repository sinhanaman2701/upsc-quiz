import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient

TEST_DB_NAME = "upsc_quiz_test"


@pytest_asyncio.fixture
async def test_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client[TEST_DB_NAME]
    yield db
    await client.drop_database(TEST_DB_NAME)
    client.close()
