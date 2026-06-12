import pytest


class TestParityFields:
    """Test parity fields: raw_text, interest_score, priority_score, cover_message, etc."""

    def test_create_trader_with_parity_fields(self, client):
        resp = client.post("/api/traders", json={
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

    def test_priority_score_calculation(self, client):
        resp = client.post("/api/traders", json={
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

    def test_priority_score_zero_interest(self, client):
        resp = client.post("/api/traders", json={
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


class TestAnalysis:
    """Test keyword analysis endpoint."""

    def test_analyze_endpoint(self, client):
        create_resp = client.post("/api/traders", json={
            "trader_name": "AnalyzeTest",
            "raw_text": "Crypto trader with 10000 followers on eToro. Specializes in DeFi yield farming strategies. High risk tolerance."
        })
        trader_id = create_resp.json()["id"]

        resp = client.post(f"/api/traders/{trader_id}/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert "keywords" in data
        assert "summary" in data
        assert len(data["keywords"]) > 0
        assert any(k in data["keywords"] for k in ["crypto", "trader", "defi", "yield", "farming"])

    def test_analyze_endpoint_empty_text(self, client):
        create_resp = client.post("/api/traders", json={
            "trader_name": "EmptyText",
            "raw_text": ""
        })
        trader_id = create_resp.json()["id"]

        resp = client.post(f"/api/traders/{trader_id}/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert data["keywords"] == []
        assert "No text" in data["summary"]

    def test_analyze_endpoint_special_characters(self, client):
        create_resp = client.post("/api/traders", json={
            "trader_name": "SpecialChars",
            "raw_text": "Trader with <script>alert('xss')</script> and &amp; entities"
        })
        trader_id = create_resp.json()["id"]

        resp = client.post(f"/api/traders/{trader_id}/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert "keywords" in data
        assert "<script>" not in str(data["keywords"])


class TestMigrationAndSecurity:
    """Test migration idempotency and XSS protection."""

    def test_migration_idempotency(self, client):
        resp = client.get("/api/traders/stats")
        assert resp.status_code == 200

        resp = client.post("/api/traders", json={"trader_name": "MigrationTest"})
        assert resp.status_code == 200

    def test_html_escaping_in_response(self, client):
        create_resp = client.post("/api/traders", json={
            "trader_name": "XSS Test",
            "raw_text": "Text with <b>bold</b> and <script>alert('xss')</script>"
        })
        assert create_resp.status_code == 200
        trader_id = create_resp.json()["id"]

        resp = client.get(f"/api/traders/{trader_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "&lt;b&gt;" in data["raw_text"]
        assert "&lt;script&gt;" in data["raw_text"]
