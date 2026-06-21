import pytest
from tests.conftest import test_db


@pytest.mark.asyncio
async def test_db_connection(test_db):
    result = await test_db.command("ping")
    assert result["ok"] == 1.0


@pytest.mark.asyncio
async def test_collections_accessible(test_db):
    await test_db["documents"].insert_one({"test": True})
    doc = await test_db["documents"].find_one({"test": True})
    assert doc is not None
