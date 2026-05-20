import pytest
from unittest.mock import patch
import app as flask_app


@pytest.fixture
def client():
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# validate_icao
# ---------------------------------------------------------------------------

class TestValidateIcao:
    def test_valid_uppercase(self):
        assert flask_app.validate_icao("LFPO") == "LFPO"

    def test_valid_lowercase_normalised(self):
        assert flask_app.validate_icao("lfpo") == "LFPO"

    def test_valid_with_whitespace(self):
        assert flask_app.validate_icao("  KJFK  ") == "KJFK"

    def test_too_short(self):
        assert flask_app.validate_icao("LFP") is None

    def test_too_long(self):
        assert flask_app.validate_icao("LFPOO") is None

    def test_contains_digits(self):
        assert flask_app.validate_icao("LF12") is None

    def test_empty_string(self):
        assert flask_app.validate_icao("") is None


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestIndexGet:
    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_contains_form(self, client):
        response = client.get("/")
        assert b"form" in response.data.lower()


# ---------------------------------------------------------------------------
# POST /
# ---------------------------------------------------------------------------

class TestIndexPost:
    def test_invalid_icao_shows_error(self, client):
        response = client.post("/", data={"icao": "LFP"})
        assert response.status_code == 200
        assert "invalide" in response.data.decode("utf-8").lower()

    def test_valid_icao_success(self, client):
        raw = "LFPO 191230Z 18015KT CAVOK 15/10 Q1013"
        with patch("app.fetch_metar", return_value=(raw, None)):
            response = client.post("/", data={"icao": "LFPO"})
        assert response.status_code == 200

    def test_fetch_error_shows_error(self, client):
        with patch("app.fetch_metar", return_value=(None, "Erreur réseau simulée")):
            response = client.post("/", data={"icao": "LFPO"})
        assert response.status_code == 200
        assert "Erreur réseau simulée" in response.data.decode("utf-8")

    def test_parse_exception_shows_error(self, client):
        raw = "LFPO 191230Z 18015KT CAVOK 15/10 Q1013"
        with patch("app.fetch_metar", return_value=(raw, None)), \
             patch("app.parse_metar", side_effect=Exception("erreur de parsing")):
            response = client.post("/", data={"icao": "LFPO"})
        assert response.status_code == 200
        assert "décodage" in response.data.decode("utf-8").lower()


# ---------------------------------------------------------------------------
# GET /api/metar/<code>
# ---------------------------------------------------------------------------

class TestApiMetar:
    def test_invalid_code_returns_400(self, client):
        response = client.get("/api/metar/LFP")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_success_returns_200_json(self, client):
        raw = "LFPO 191230Z 18015KT CAVOK 15/10 Q1013"
        parsed = {"station": "LFPO", "raw": raw, "error": None}
        with patch("app.fetch_metar", return_value=(raw, None)), \
             patch("app.parse_metar", return_value=parsed):
            response = client.get("/api/metar/LFPO")
        assert response.status_code == 200
        assert response.get_json()["station"] == "LFPO"

    def test_fetch_error_returns_502(self, client):
        with patch("app.fetch_metar", return_value=(None, "Serveur indisponible")):
            response = client.get("/api/metar/LFPO")
        assert response.status_code == 502
        assert "error" in response.get_json()

    def test_parse_exception_returns_500(self, client):
        raw = "LFPO 191230Z 18015KT CAVOK 15/10 Q1013"
        with patch("app.fetch_metar", return_value=(raw, None)), \
             patch("app.parse_metar", side_effect=Exception("boom")):
            response = client.get("/api/metar/LFPO")
        assert response.status_code == 500
        assert "error" in response.get_json()
