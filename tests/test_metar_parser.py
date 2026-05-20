import pytest
from metar_parser import (
    degrees_to_compass,
    parse_time,
    parse_wind,
    parse_visibility,
    parse_phenomena,
    parse_clouds,
    parse_temp_dewpoint,
    parse_pressure,
    parse_trend,
    choose_icon,
    build_summary,
    parse_metar,
)


# ---------------------------------------------------------------------------
# degrees_to_compass
# ---------------------------------------------------------------------------

class TestDegreesToCompass:
    def test_north_zero(self):
        assert degrees_to_compass(0) == "Nord"

    def test_north_360(self):
        assert degrees_to_compass(360) == "Nord"

    def test_north_east(self):
        assert degrees_to_compass(45) == "Nord-Est"

    def test_east(self):
        assert degrees_to_compass(90) == "Est"

    def test_south_east(self):
        assert degrees_to_compass(135) == "Sud-Est"

    def test_south(self):
        assert degrees_to_compass(180) == "Sud"

    def test_south_west(self):
        assert degrees_to_compass(225) == "Sud-Ouest"

    def test_west(self):
        assert degrees_to_compass(270) == "Ouest"

    def test_north_west(self):
        assert degrees_to_compass(315) == "Nord-Ouest"

    def test_boundary_22_is_north(self):
        assert degrees_to_compass(22) == "Nord"

    def test_boundary_23_is_north_east(self):
        assert degrees_to_compass(23) == "Nord-Est"

    def test_boundary_67_is_north_east(self):
        assert degrees_to_compass(67) == "Nord-Est"

    def test_boundary_68_is_east(self):
        assert degrees_to_compass(68) == "Est"


# ---------------------------------------------------------------------------
# parse_time
# ---------------------------------------------------------------------------

class TestParseTime:
    def test_valid_token(self):
        result = parse_time("191230Z")
        assert result["day"] == 19
        assert result["hour"] == 12
        assert result["minute"] == 30
        assert "19" in result["fr"]

    def test_invalid_token_returns_raw(self):
        result = parse_time("ABCDE")
        assert result["raw"] == "ABCDE"
        assert result["fr"] == "ABCDE"


# ---------------------------------------------------------------------------
# parse_wind
# ---------------------------------------------------------------------------

class TestParseWind:
    def test_normal_wind_kt(self):
        wind, idx = parse_wind(["18015KT"], 0)
        assert wind is not None
        assert wind["direction_deg"] == 180
        assert wind["speed"] == 15
        assert wind["unit"] == "nœuds"
        assert idx == 1

    def test_wind_with_gust(self):
        wind, idx = parse_wind(["18015G25KT"], 0)
        assert wind["gust"] == 25

    def test_variable_wind(self):
        wind, idx = parse_wind(["VRB10KT"], 0)
        assert wind["direction_fr"] == "variable"
        assert wind["direction_deg"] is None

    def test_calm_wind(self):
        wind, idx = parse_wind(["00000KT"], 0)
        assert wind["calm"] is True
        assert "calme" in wind["fr"]

    def test_kmh_unit(self):
        wind, idx = parse_wind(["18015KMH"], 0)
        assert wind["unit"] == "km/h"

    def test_mps_unit(self):
        wind, idx = parse_wind(["18010MPS"], 0)
        assert wind["unit"] == "m/s"

    def test_non_wind_token_returns_none(self):
        wind, idx = parse_wind(["9999"], 0)
        assert wind is None
        assert idx == 0

    def test_empty_tokens_returns_none(self):
        wind, idx = parse_wind([], 0)
        assert wind is None
        assert idx == 0

    def test_idx_beyond_length(self):
        wind, idx = parse_wind(["18015KT"], 5)
        assert wind is None
        assert idx == 5


# ---------------------------------------------------------------------------
# parse_visibility
# ---------------------------------------------------------------------------

class TestParseVisibility:
    def test_9999_greater_than_10km(self):
        vis, idx = parse_visibility(["9999"], 0)
        assert "10 km" in vis["fr"]
        assert idx == 1

    def test_meters_under_1000(self):
        vis, idx = parse_visibility(["0500"], 0)
        assert "500 m" in vis["fr"]

    def test_km_exact(self):
        vis, idx = parse_visibility(["5000"], 0)
        assert "5 km" in vis["fr"]

    def test_statute_miles_whole(self):
        vis, idx = parse_visibility(["10SM"], 0)
        assert "km" in vis["fr"]
        assert idx == 1

    def test_statute_miles_fraction(self):
        vis, idx = parse_visibility(["1/2SM"], 0)
        assert "km" in vis["fr"]

    def test_rvr_tokens_skipped(self):
        tokens = ["0600", "R28L/0600", "RA"]
        vis, idx = parse_visibility(tokens, 0)
        assert idx == 2

    def test_non_visibility_token_returns_none(self):
        vis, idx = parse_visibility(["LFPO"], 0)
        assert vis is None
        assert idx == 0


# ---------------------------------------------------------------------------
# parse_phenomena
# ---------------------------------------------------------------------------

class TestParsePhenomena:
    def test_simple_rain(self):
        phenomena, idx = parse_phenomena(["RA"], 0)
        assert len(phenomena) == 1
        assert phenomena[0]["code"] == "RA"
        assert "pluie" in phenomena[0]["fr"]

    def test_light_intensity(self):
        phenomena, idx = parse_phenomena(["-RA"], 0)
        assert "légère" in phenomena[0]["fr"]

    def test_heavy_intensity(self):
        phenomena, idx = parse_phenomena(["+TS"], 0)
        assert "forte" in phenomena[0]["fr"]

    def test_shower_descriptor(self):
        phenomena, idx = parse_phenomena(["SHRA"], 0)
        assert "averses" in phenomena[0]["fr"]

    def test_thunderstorm_descriptor(self):
        phenomena, idx = parse_phenomena(["TSRA"], 0)
        assert "orage" in phenomena[0]["fr"]

    def test_freezing_descriptor(self):
        phenomena, idx = parse_phenomena(["FZRA"], 0)
        assert "verglaçant" in phenomena[0]["fr"]

    def test_recent_weather_prefix(self):
        phenomena, idx = parse_phenomena(["RERA"], 0)
        assert phenomena[0]["fr"].startswith("Récemment")

    def test_vicinity(self):
        phenomena, idx = parse_phenomena(["VCFG"], 0)
        assert "environs" in phenomena[0]["fr"]

    def test_multiple_phenomena(self):
        phenomena, idx = parse_phenomena(["RA", "SN"], 0)
        assert len(phenomena) == 2

    def test_non_phenomenon_stops_loop(self):
        phenomena, idx = parse_phenomena(["RA", "BKN025"], 0)
        assert len(phenomena) == 1
        assert idx == 1


# ---------------------------------------------------------------------------
# parse_clouds
# ---------------------------------------------------------------------------

class TestParseClouds:
    def test_skc_clear(self):
        clouds, idx = parse_clouds(["SKC"], 0)
        assert clouds[0]["cover"] == "SKC"
        assert "dégagé" in clouds[0]["fr"]

    def test_bkn_with_height(self):
        clouds, idx = parse_clouds(["BKN025"], 0)
        assert clouds[0]["height_ft"] == 2500
        assert clouds[0]["height_m"] == 762

    def test_few_cb(self):
        clouds, idx = parse_clouds(["FEW030CB"], 0)
        assert "cumulo-nimbus" in clouds[0]["fr"]

    def test_sct_tcu(self):
        clouds, idx = parse_clouds(["SCT040TCU"], 0)
        assert "cumulus bourgeonnant" in clouds[0]["fr"]

    def test_vertical_visibility(self):
        clouds, idx = parse_clouds(["VV002"], 0)
        assert clouds[0]["cover"] == "VV"
        assert clouds[0]["height_ft"] == 200

    def test_non_cloud_token_stops(self):
        clouds, idx = parse_clouds(["BKN025", "15/10"], 0)
        assert len(clouds) == 1
        assert idx == 1


# ---------------------------------------------------------------------------
# parse_temp_dewpoint
# ---------------------------------------------------------------------------

class TestParseTempDewpoint:
    def test_positive_temps(self):
        temp, dew, idx = parse_temp_dewpoint(["15/10"], 0)
        assert temp == 15
        assert dew == 10
        assert idx == 1

    def test_both_negative(self):
        temp, dew, idx = parse_temp_dewpoint(["M05/M10"], 0)
        assert temp == -5
        assert dew == -10

    def test_mixed_signs(self):
        temp, dew, idx = parse_temp_dewpoint(["02/M01"], 0)
        assert temp == 2
        assert dew == -1

    def test_invalid_token_returns_none(self):
        temp, dew, idx = parse_temp_dewpoint(["Q1013"], 0)
        assert temp is None
        assert dew is None
        assert idx == 0


# ---------------------------------------------------------------------------
# parse_pressure
# ---------------------------------------------------------------------------

class TestParsePressure:
    def test_q_format(self):
        pressure, idx = parse_pressure(["Q1013"], 0)
        assert pressure["hpa"] == 1013
        assert "1013 hPa" in pressure["fr"]
        assert idx == 1

    def test_a_format(self):
        pressure, idx = parse_pressure(["A2992"], 0)
        assert pressure["inhg"] == 29.92
        assert "inHg" in pressure["fr"]
        assert idx == 1

    def test_invalid_token_returns_none(self):
        pressure, idx = parse_pressure(["BKN025"], 0)
        assert pressure is None
        assert idx == 0


# ---------------------------------------------------------------------------
# parse_trend
# ---------------------------------------------------------------------------

class TestParseTrend:
    def test_nosig(self):
        result = parse_trend(["NOSIG"], 0)
        assert "significatif" in result

    def test_tempo_with_rest(self):
        result = parse_trend(["TEMPO", "SHRA"], 0)
        assert "Temporairement" in result
        assert "SHRA" in result

    def test_becmg_with_rest(self):
        result = parse_trend(["BECMG", "BKN010"], 0)
        assert "Évolution" in result
        assert "BKN010" in result

    def test_empty_returns_none(self):
        result = parse_trend([], 0)
        assert result is None


# ---------------------------------------------------------------------------
# choose_icon
# ---------------------------------------------------------------------------

class TestChooseIcon:
    def _make_result(self, phenomena_codes=None, clouds=None, cavok=False):
        phenomena = [{"code": c} for c in (phenomena_codes or [])]
        cloud_list = [{"cover": c} for c in (clouds or [])]
        return {"phenomena": phenomena, "clouds": cloud_list, "cavok": cavok}

    def test_thunderstorm_priority(self):
        result = self._make_result(["TS", "RA"])
        assert choose_icon(result) == "⛈️"

    def test_snow(self):
        assert choose_icon(self._make_result(["SN"])) == "❄️"

    def test_rain(self):
        assert choose_icon(self._make_result(["RA"])) == "🌧️"

    def test_fog(self):
        assert choose_icon(self._make_result(["FG"])) == "🌫️"

    def test_cavok_returns_sun(self):
        assert choose_icon(self._make_result(cavok=True)) == "☀️"

    def test_overcast_cloud(self):
        assert choose_icon(self._make_result(clouds=["OVC"])) == "☁️"

    def test_few_cloud(self):
        assert choose_icon(self._make_result(clouds=["FEW"])) == "🌤️"

    def test_no_phenomena_no_clouds(self):
        assert choose_icon(self._make_result()) == "☀️"


# ---------------------------------------------------------------------------
# build_summary
# ---------------------------------------------------------------------------

class TestBuildSummary:
    def _base_result(self):
        return {
            "cavok": False,
            "phenomena": [],
            "clouds": [],
            "temperature": None,
            "dewpoint": None,
            "wind": None,
            "pressure": None,
            "visibility": None,
        }

    def test_cavok_summary(self):
        r = self._base_result()
        r["cavok"] = True
        assert "CAVOK" in build_summary(r)

    def test_temp_and_wind(self):
        r = self._base_result()
        r["temperature"] = 15
        r["dewpoint"] = 10
        r["wind"] = {"calm": False, "fr": "10 nœuds vers le Sud"}
        summary = build_summary(r)
        assert "15" in summary
        assert "vent" in summary

    def test_calm_wind(self):
        r = self._base_result()
        r["wind"] = {"calm": True, "fr": "vent calme"}
        assert "calme" in build_summary(r)

    def test_pressure_in_summary(self):
        r = self._base_result()
        r["pressure"] = {"fr": "1013 hPa"}
        assert "1013" in build_summary(r)


# ---------------------------------------------------------------------------
# parse_metar (end-to-end)
# ---------------------------------------------------------------------------

class TestParseMetar:
    def test_full_metar(self):
        raw = "LFPO 191230Z 18015KT 9999 BKN025 15/10 Q1013 NOSIG"
        result = parse_metar(raw)
        assert result["station"] == "LFPO"
        assert result["wind"]["speed"] == 15
        assert result["temperature"] == 15
        assert result["dewpoint"] == 10
        assert result["pressure"]["hpa"] == 1013
        assert result["error"] is None

    def test_metar_prefix_stripped(self):
        raw = "METAR KJFK 191230Z 27010KT 9999 SKC 20/10 Q1015"
        result = parse_metar(raw)
        assert result["station"] == "KJFK"

    def test_auto_flag(self):
        raw = "LFPG AUTO 191230Z 18015KT 9999 SKC 15/10 Q1013"
        result = parse_metar(raw)
        assert result["auto"] is True

    def test_cavok(self):
        raw = "LFPO 191230Z 18015KT CAVOK 15/10 Q1013"
        result = parse_metar(raw)
        assert result["cavok"] is True

    def test_empty_string_returns_error(self):
        result = parse_metar("")
        assert result["error"] is not None

    def test_incomplete_metar_returns_error(self):
        result = parse_metar("METAR")
        assert result["error"] is not None

    def test_negative_temp(self):
        raw = "LFPO 191230Z 18015KT 9999 SKC M05/M10 Q1013"
        result = parse_metar(raw)
        assert result["temperature"] == -5
        assert result["dewpoint"] == -10

    def test_inhg_pressure(self):
        raw = "KJFK 191230Z 27010KT 9999 SKC 20/10 A2992"
        result = parse_metar(raw)
        assert result["pressure"]["inhg"] == 29.92

    def test_multiple_phenomena(self):
        raw = "LFPO 191230Z 18015KT 5000 RA SN BKN015 10/08 Q1010"
        result = parse_metar(raw)
        assert len(result["phenomena"]) == 2
