import pytest
import pytest_asyncio
import sqlite3
from httpx import AsyncClient, ASGITransport
from main import app
from database import init_db


@pytest_asyncio.fixture
async def async_client(test_db):
    await init_db()
    conn = sqlite3.connect(str(test_db))
    conn.execute("DELETE FROM outreach_logs")
    conn.execute("DELETE FROM traders")
    conn.commit()
    conn.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_trader_with_parity_fields(async_client):
    resp = await async_client.post("/api/traders", json={
        "trader_name": "TestTrader",
        "platform": "eToro",
        "raw_text": "Test raw text content",
        "interest_score": 4,
        "cover_message": "Hello, we'd love to collaborate",
        "response_received": "Yes",
        "stage_reached": "Interview"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["raw_text"] == "Test raw text content"
    assert data["interest_score"] == 4
    assert data["priority_score"] == data["fit_score"] * 4 // 5
    assert data["cover_message"] == "Hello, we'd love to collaborate"
    assert data["response_received"] == "Yes"
    assert data["stage_reached"] == "Interview"


@pytest.mark.asyncio
async def test_priority_score_calculation(async_client):
    resp = await async_client.post("/api/traders", json={
        "trader_name": "PriorityTest",
        "interest_score": 5,
        "audience_strength": 10,
        "trading_consistency": 10,
        "communication_quality": 10,
        "crypto_knowledge": 10,
        "likelihood_to_join": 10,
        "brand_value": 10
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["fit_score"] == 100
    assert data["priority_score"] == 100


@pytest.mark.asyncio
async def test_priority_score_zero_interest(async_client):
    resp = await async_client.post("/api/traders", json={
        "trader_name": "ZeroInterest",
        "interest_score": 0,
        "audience_strength": 10,
        "trading_consistency": 10,
        "communication_quality": 10,
        "crypto_knowledge": 10,
        "likelihood_to_join": 10,
        "brand_value": 10
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["priority_score"] == 0


@pytest.mark.asyncio
async def test_analyze_endpoint(async_client):
    create_resp = await async_client.post("/api/traders", json={
        "trader_name": "AnalyzeTest",
        "raw_text": "Crypto trader with 10000 followers on eToro. Specializes in DeFi yield farming strategies. High risk tolerance."
    })
    trader_id = create_resp.json()["id"]

    resp = await async_client.post(f"/api/traders/{trader_id}/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert "keywords" in data
    assert "summary" in data
    assert len(data["keywords"]) > 0
    assert any(k in data["keywords"] for k in ["crypto", "trader", "defi", "yield", "farming"])


@pytest.mark.asyncio
async def test_analyze_endpoint_empty_text(async_client):
    create_resp = await async_client.post("/api/traders", json={
        "trader_name": "EmptyText",
        "raw_text": ""
    })
    trader_id = create_resp.json()["id"]

    resp = await async_client.post(f"/api/traders/{trader_id}/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert data["keywords"] == []
    assert "No text" in data["summary"]


@pytest.mark.asyncio
async def test_analyze_endpoint_special_characters(async_client):
    create_resp = await async_client.post("/api/traders", json={
        "trader_name": "SpecialChars",
        "raw_text": "Trader with <script>alert('xss')</script> and &amp; entities"
    })
    trader_id = create_resp.json()["id"]

    resp = await async_client.post(f"/api/traders/{trader_id}/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert "keywords" in data
    assert "<script>" not in str(data["keywords"])


@pytest.mark.asyncio
async def test_migration_idempotency(async_client):
    resp = await async_client.get("/api/traders/stats")
    assert resp.status_code == 200

    resp = await async_client.post("/api/traders", json={"trader_name": "MigrationTest"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_html_escaping_in_response(async_client):
    create_resp = await async_client.post("/api/traders", json={
        "trader_name": "XSS Test",
        "raw_text": "Text with <b>bold</b> and <script>alert('xss')</script>"
    })
    assert create_resp.status_code == 200
    trader_id = create_resp.json()["id"]

    resp = await async_client.get(f"/api/traders/{trader_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "&lt;b&gt;" in data["raw_text"]
    assert "&lt;script&gt;" in data["raw_text"]
