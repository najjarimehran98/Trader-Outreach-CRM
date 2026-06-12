import pytest


class TestCreateTrader:
    """Test 1: POST /api/traders creates a trader and returns it."""

    def test_create_trader_returns_trader_with_id(self, client):
        payload = {
            "trader_name": "TestTrader",
            "platform": "eToro",
            "profile_url": "https://etoro.com/testtrader",
            "location": "Test City",
            "followers": 1000,
            "monthly_return": 5.0,
            "audience_strength": 7,
            "trading_consistency": 8,
            "communication_quality": 6,
            "crypto_knowledge": 5,
            "likelihood_to_join": 4,
            "brand_value": 6,
        }
        resp = client.post("/api/traders", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["trader_name"] == "TestTrader"
        assert data["platform"] == "eToro"
        assert data["id"] is not None
        assert data["status"] == "Trader Found"
        assert data["date_added"] is not None
        assert data["fit_score"] > 0

    def test_create_trader_stores_in_database(self, client):
        payload = {"trader_name": "DBCheck", "platform": "Manual"}
        client.post("/api/traders", json=payload)
        resp = client.get("/api/traders")
        traders = resp.json()
        names = [t["trader_name"] for t in traders]
        assert "DBCheck" in names


class TestGetTrader:
    """Test 2: GET /api/traders/{id} returns a single trader."""

    def test_get_trader_by_id(self, client):
        payload = {"trader_name": "GetMe", "platform": "MQL5"}
        create_resp = client.post("/api/traders", json=payload)
        trader_id = create_resp.json()["id"]

        resp = client.get(f"/api/traders/{trader_id}")
        assert resp.status_code == 200
        assert resp.json()["trader_name"] == "GetMe"
        assert resp.json()["platform"] == "MQL5"

    def test_get_nonexistent_trader_returns_404(self, client):
        resp = client.get("/api/traders/nonexistent_id")
        assert resp.status_code == 404

    def test_get_trader_includes_outreach_logs(self, client):
        payload = {"trader_name": "WithLogs", "platform": "Manual"}
        create_resp = client.post("/api/traders", json=payload)
        trader_id = create_resp.json()["id"]

        resp = client.get(f"/api/traders/{trader_id}")
        assert "outreach_logs" in resp.json()


class TestStats:
    """Test 3: GET /api/traders/stats returns correct statistics."""

    def test_stats_returns_all_fields(self, client):
        resp = client.get("/api/traders/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "active_pipeline" in data
        assert "total_outreach" in data
        assert "reply_rate" in data
        assert "by_status" in data
        assert "by_platform" in data
        assert "conversion_rate" in data

    def test_stats_reflects_actual_data(self, client):
        # Create traders with known statuses
        client.post("/api/traders", json={"trader_name": "A", "platform": "eToro", "status": "Contacted"})
        client.post("/api/traders", json={"trader_name": "B", "platform": "MQL5", "status": "Replied"})
        client.post("/api/traders", json={"trader_name": "C", "platform": "eToro", "status": "Rejected"})

        resp = client.get("/api/traders/stats")
        data = resp.json()
        assert data["total"] == 3
        assert data["by_status"]["Contacted"] == 1
        assert data["by_status"]["Replied"] == 1
        assert data["by_status"]["Rejected"] == 1
        assert data["by_platform"]["eToro"] == 2
        assert data["by_platform"]["MQL5"] == 1
        # Reply rate = replied / (contacted + replied) = 1 / (1+1) = 50%
        assert data["reply_rate"] == 50.0


class TestOutreach:
    """Test 4: POST /api/traders/{id}/outreach logs outreach and increments count."""

    def test_log_outreach_increments_attempts(self, client):
        payload = {"trader_name": "OutreachTest", "platform": "Manual"}
        create_resp = client.post("/api/traders", json=payload)
        trader_id = create_resp.json()["id"]
        assert create_resp.json()["outreach_attempts"] == 0

        resp = client.post(f"/api/traders/{trader_id}/outreach", json={
            "method": "email",
            "notes": "Sent intro email"
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # Verify attempts incremented
        get_resp = client.get(f"/api/traders/{trader_id}")
        assert get_resp.json()["outreach_attempts"] == 1
        assert get_resp.json()["last_contact_date"] is not None

    def test_log_outreach_stores_in_outreach_logs(self, client):
        payload = {"trader_name": "LogCheck", "platform": "Manual"}
        create_resp = client.post("/api/traders", json=payload)
        trader_id = create_resp.json()["id"]

        client.post(f"/api/traders/{trader_id}/outreach", json={
            "method": "telegram",
            "notes": "DM sent"
        })

        get_resp = client.get(f"/api/traders/{trader_id}")
        logs = get_resp.json()["outreach_logs"]
        assert len(logs) == 1
        assert logs[0]["method"] == "telegram"
        assert logs[0]["notes"] == "DM sent"

    def test_multiple_outreach_increments_correctly(self, client):
        payload = {"trader_name": "MultiOutreach", "platform": "Manual"}
        create_resp = client.post("/api/traders", json=payload)
        trader_id = create_resp.json()["id"]

        client.post(f"/api/traders/{trader_id}/outreach", json={"method": "email", "notes": "1"})
        client.post(f"/api/traders/{trader_id}/outreach", json={"method": "twitter", "notes": "2"})
        client.post(f"/api/traders/{trader_id}/outreach", json={"method": "discord", "notes": "3"})

        get_resp = client.get(f"/api/traders/{trader_id}")
        assert get_resp.json()["outreach_attempts"] == 3
        assert len(get_resp.json()["outreach_logs"]) == 3

    def test_outreach_nonexistent_trader_returns_404(self, client):
        resp = client.post("/api/traders/fake_id/outreach", json={"method": "email"})
        assert resp.status_code == 404


class TestFitScore:
    """Test 5: Fit score is calculated correctly from scoring fields."""

    def test_fit_score_uses_weighted_average(self, client):
        payload = {
            "trader_name": "ScoreTest",
            "platform": "Manual",
            "audience_strength": 10,
            "trading_consistency": 10,
            "communication_quality": 10,
            "crypto_knowledge": 10,
            "likelihood_to_join": 10,
            "brand_value": 10,
        }
        resp = client.post("/api/traders", json=payload)
        # All 10s with default weights (1.0) = 100%
        assert resp.json()["fit_score"] == 100

    def test_fit_score_zero_when_all_zero(self, client):
        payload = {
            "trader_name": "ZeroScore",
            "platform": "Manual",
            "audience_strength": 0,
            "trading_consistency": 0,
            "communication_quality": 0,
            "crypto_knowledge": 0,
            "likelihood_to_join": 0,
            "brand_value": 0,
        }
        resp = client.post("/api/traders", json=payload)
        assert resp.json()["fit_score"] == 0

    def test_fit_score_updates_when_scoring_fields_change(self, client):
        payload = {
            "trader_name": "UpdateScore",
            "platform": "Manual",
            "audience_strength": 5,
            "trading_consistency": 5,
            "communication_quality": 5,
            "crypto_knowledge": 5,
            "likelihood_to_join": 5,
            "brand_value": 5,
        }
        create_resp = client.post("/api/traders", json=payload)
        trader_id = create_resp.json()["id"]
        assert create_resp.json()["fit_score"] == 50  # 5/10 = 50%

        # Update to 10s
        client.put(f"/api/traders/{trader_id}", json={
            "audience_strength": 10,
            "trading_consistency": 10,
            "communication_quality": 10,
            "crypto_knowledge": 10,
            "likelihood_to_join": 10,
            "brand_value": 10,
        })
        get_resp = client.get(f"/api/traders/{trader_id}")
        assert get_resp.json()["fit_score"] == 100

    def test_fit_score_uneven_scores(self, client):
        payload = {
            "trader_name": "UnevenScore",
            "platform": "Manual",
            "audience_strength": 10,
            "trading_consistency": 0,
            "communication_quality": 0,
            "crypto_knowledge": 0,
            "likelihood_to_join": 0,
            "brand_value": 0,
        }
        resp = client.post("/api/traders", json=payload)
        # 10*1.0 / (10*6) * 100 = 16.67 -> rounds to 17
        assert resp.json()["fit_score"] == 17
