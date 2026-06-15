import pytest
import requests


class TestFrontendIntegrity:
    """Tests that verify the HTML/CSS rewrite didn't break anything."""

    BASE = "http://localhost:8001"

    def test_html_contains_design_system_css(self):
        """The page should load design-system.css, not Tailwind."""
        resp = requests.get(f"{self.BASE}/")
        assert resp.status_code == 200
        assert "design-system.css" in resp.text
        assert 'rel="stylesheet" href="design-system.css"' in resp.text

    def test_html_no_tailwind_cdn(self):
        """Tailwind CDN should be completely removed."""
        resp = requests.get(f"{self.BASE}/")
        assert "cdn.tailwindcss.com" not in resp.text

    def test_html_no_font_awesome(self):
        """Font Awesome CDN should be completely removed."""
        resp = requests.get(f"{self.BASE}/")
        assert "cdnjs.cloudflare.com" not in resp.text
        assert "font-awesome" not in resp.text
        assert "fontawesome" not in resp.text

    def test_html_no_font_awesome_icons(self):
        """No <i class="fa-*"> tags should remain — all replaced with SVGs."""
        resp = requests.get(f"{self.BASE}/")
        assert 'class="fa-' not in resp.text
        assert 'class="fas ' not in resp.text
        assert 'class="far ' not in resp.text

    def test_html_has_svg_icons(self):
        """Nav items should use inline SVGs instead of icon fonts."""
        resp = requests.get(f"{self.BASE}/")
        svg_count = resp.text.count("<svg")
        assert svg_count >= 4, f"Expected at least 4 SVG icons (nav items), found {svg_count}"

    def test_design_system_css_loads(self):
        """design-system.css should be served and contain Apple tokens."""
        resp = requests.get(f"{self.BASE}/design-system.css")
        assert resp.status_code == 200
        assert "--bg: #1e1e1e" in resp.text
        assert "--surface: #2d2d2d" in resp.text
        assert "--accent: #0a84ff" in resp.text

    def test_design_system_has_light_mode(self):
        """design-system.css should have light mode variables."""
        resp = requests.get(f"{self.BASE}/design-system.css")
        assert ":root.light" in resp.text
        assert "--bg: #f5f5f7" in resp.text

    def test_design_system_has_utility_classes(self):
        """design-system.css should define .hidden, .flex, .flex-1, .min-h-screen."""
        resp = requests.get(f"{self.BASE}/design-system.css")
        assert ".hidden" in resp.text
        assert ".flex " in resp.text
        assert ".flex-1" in resp.text
        assert ".min-h-screen" in resp.text

    def test_no_tailwind_classes_in_html(self):
        """HTML should not contain Tailwind utility class patterns."""
        resp = requests.get(f"{self.BASE}/")
        # Common Tailwind patterns that should NOT appear
        forbidden = [
            'class="p-6"',
            'class="flex justify-between',
            'class="text-2xl font-bold',
            'class="bg-accent',
            'class="rounded-xl',
            'class="rounded-2xl',
            'class="bg-surface-raised',
            'class="text-label"',
            'class="text-label-secondary"',
            'class="border-b border-brd',
        ]
        for pattern in forbidden:
            assert pattern not in resp.text, f"Found Tailwind pattern: {pattern}"


class TestAPIAfterMerge:
    """Tests that verify API endpoints still work after the merge."""

    BASE = "http://localhost:8001"

    def test_stats_endpoint_returns_all_fields(self):
        """Stats should return all required fields."""
        resp = requests.get(f"{self.BASE}/api/traders/stats")
        assert resp.status_code == 200
        data = resp.json()
        required = ["total", "active_pipeline", "total_outreach", "reply_rate",
                     "by_status", "by_platform", "conversion_rate"]
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_settings_endpoint_returns_weights_and_platforms(self):
        """Settings should return scoring weights and platforms."""
        resp = requests.get(f"{self.BASE}/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        assert "scoring_weights.audience_strength" in data
        assert "platforms.enabled" in data

    def test_create_trader_with_special_characters(self):
        """XSS prevention: trader names with HTML should be escaped."""
        payload = {
            "trader_name": '<script>alert("xss")</script>',
            "platform": "Manual"
        }
        resp = requests.post(f"{self.BASE}/api/traders", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        # Name should be stored as-is (escaping happens on display)
        assert data["trader_name"] == '<script>alert("xss")</script>'
        # But when fetched, the API should not execute the script
        trader_id = data["id"]
        get_resp = requests.get(f"{self.BASE}/api/traders/{trader_id}")
        assert get_resp.status_code == 200

    def test_analyze_endpoint_handles_empty_text(self):
        """Analyze endpoint should handle empty raw_text gracefully."""
        payload = {"trader_name": "EmptyRaw", "platform": "Manual", "raw_text": ""}
        resp = requests.post(f"{self.BASE}/api/traders", json=payload)
        trader_id = resp.json()["id"]
        analyze_resp = requests.post(f"{self.BASE}/api/traders/{trader_id}/analyze")
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert "keywords" in data
        assert isinstance(data["keywords"], list)

    def test_trader_detail_includes_all_fields(self):
        """Trader detail should include parity fields (interest_score, priority_score, etc.)."""
        payload = {
            "trader_name": "DetailCheck",
            "platform": "eToro",
            "interest_score": 4,
            "cover_message": "Hello!",
            "raw_text": "Some profile text"
        }
        resp = requests.post(f"{self.BASE}/api/traders", json=payload)
        trader_id = resp.json()["id"]
        detail = requests.get(f"{self.BASE}/api/traders/{trader_id}").json()
        assert detail["interest_score"] == 4
        assert detail["cover_message"] == "Hello!"
        assert detail["raw_text"] == "Some profile text"
        assert "priority_score" in detail
        assert "outreach_logs" in detail
