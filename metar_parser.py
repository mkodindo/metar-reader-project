import re

WEATHER_CODES = {
    "RA": "pluie",
    "SN": "neige",
    "FG": "brouillard",
    "BR": "brume",
    "TS": "orage",
    "DZ": "bruine",
    "GR": "grêle",
    "GS": "grésil",
    "SG": "neige en grains",
    "IC": "cristaux de glace",
    "PL": "pluie verglaçante",
    "UP": "précipitations inconnues",
    "HZ": "brume sèche",
    "FU": "fumée",
    "DU": "poussière",
    "SA": "sable",
    "VA": "cendres volcaniques",
    "SQ": "grain",
    "FC": "trombe",
    "SS": "tempête de sable",
    "DS": "tempête de poussière",
    # Descriptors
    "MI": "mince",
    "BC": "bancs de",
    "PR": "partiel",
    "DR": "chasse-neige basse",
    "BL": "chasse-neige haute",
    "SH": "averses de",
    "FZ": "verglaçant",
}

INTENSITY = {
    "-": "légère",
    "+": "forte",
    "VC": "dans les environs",
}

CLOUD_COVER = {
    "SKC": ("dégagé", 0),
    "CLR": ("dégagé", 0),
    "NSC": ("pas de nuages significatifs", 0),
    "NCD": ("pas de nuages détectés", 0),
    "FEW": ("quelques nuages", 1),
    "SCT": ("nuages épars", 2),
    "BKN": ("ciel couvert", 3),
    "OVC": ("ciel complètement couvert", 4),
}

ICON_MAP = {
    "TS":  "⛈️",
    "SN":  "❄️",
    "GR":  "❄️",
    "RA":  "🌧️",
    "DZ":  "🌦️",
    "FG":  "🌫️",
    "BR":  "🌫️",
    "HZ":  "🌫️",
    "OVC": "☁️",
    "BKN": "⛅",
    "SCT": "⛅",
    "FEW": "🌤️",
    "SKC": "☀️",
    "CLR": "☀️",
    "NSC": "☀️",
    "NCD": "☀️",
}

TREND_MAP = {
    "NOSIG": "Aucun changement significatif prévu",
    "BECMG": "Évolution progressive vers",
    "TEMPO": "Temporairement",
    "INTER": "Intermittent",
}

WX_PATTERN = re.compile(
    r'^([-+]|VC)?'
    r'(MI|BC|PR|DR|BL|SH|TS|FZ)?'
    r'(RA|SN|FG|BR|DZ|GR|GS|SG|IC|PL|UP|HZ|FU|DU|SA|VA|SQ|FC|SS|DS|TS)'
    r'(RA|SN|FG|BR|DZ|GR|GS)?$'
)

CLOUD_PATTERN = re.compile(r'^(SKC|CLR|NSC|NCD|FEW|SCT|BKN|OVC)(\d{3})?(CB|TCU)?$')


def degrees_to_compass(deg: int) -> str:
    deg = deg % 360
    sectors = [
        (0,   22,  "Nord"),
        (23,  67,  "Nord-Est"),
        (68,  112, "Est"),
        (113, 157, "Sud-Est"),
        (158, 202, "Sud"),
        (203, 247, "Sud-Ouest"),
        (248, 292, "Ouest"),
        (293, 337, "Nord-Ouest"),
        (338, 360, "Nord"),
    ]
    for lo, hi, name in sectors:
        if lo <= deg <= hi:
            return name
    return "Nord"


def parse_time(token: str) -> dict:
    m = re.match(r'^(\d{2})(\d{2})(\d{2})Z$', token)
    if not m:
        return {"raw": token, "fr": token}
    day, hour, minute = int(m[1]), int(m[2]), int(m[3])
    return {
        "raw": token,
        "day": day,
        "hour": hour,
        "minute": minute,
        "fr": f"le {day} à {hour:02d}h{minute:02d} UTC",
    }


def parse_wind(tokens: list, idx: int) -> tuple:
    if idx >= len(tokens):
        return None, idx
    token = tokens[idx]
    m = re.match(r'^(VRB|\d{3})(\d{2,3})(?:G(\d{2,3}))?(KT|KMH|MPS)$', token)
    if not m:
        return None, idx
    direction_raw, speed_raw, gust_raw, unit = m[1], m[2], m[3], m[4]
    speed = int(speed_raw)
    gust = int(gust_raw) if gust_raw else None

    unit_fr = {"KT": "nœuds", "KMH": "km/h", "MPS": "m/s"}.get(unit, unit)

    if direction_raw == "000" and speed == 0:
        return {"raw": token, "calm": True, "fr": "vent calme"}, idx + 1

    if direction_raw == "VRB":
        direction_fr = "variable"
        direction_deg = None
    else:
        direction_deg = int(direction_raw)
        direction_fr = degrees_to_compass(direction_deg)

    article = "l'" if direction_fr[0] in "AEIOU" else "le "
    fr = f"{speed} {unit_fr} vers {article}{direction_fr}"
    if gust:
        fr += f" (rafales à {gust} {unit_fr})"

    return {
        "raw": token,
        "direction_deg": direction_deg,
        "direction_fr": direction_fr,
        "speed": speed,
        "gust": gust,
        "unit": unit_fr,
        "fr": fr,
    }, idx + 1


def parse_visibility(tokens: list, idx: int) -> tuple:
    if idx >= len(tokens):
        return None, idx
    token = tokens[idx]

    # 4-digit meters
    if re.match(r'^\d{4}$', token):
        vis_m = int(token)
        if vis_m == 9999:
            fr = "supérieure à 10 km"
        elif vis_m >= 1000:
            km = vis_m / 1000
            fr = f"{km:.0f} km" if km == int(km) else f"{km:.1f} km"
        else:
            fr = f"{vis_m} m"
        idx += 1
        # Skip RVR tokens (R\d{2}[LCR]?/...)
        while idx < len(tokens) and re.match(r'^R\d{2}[LCR]?/', tokens[idx]):
            idx += 1
        return {"raw": token, "meters": vis_m, "fr": fr}, idx

    # US statute miles (e.g. 10SM, 1/2SM)
    m = re.match(r'^(\d+(?:/\d+)?)SM$', token)
    if m:
        val_str = m[1]
        if '/' in val_str:
            num, den = val_str.split('/')
            val_km = (int(num) / int(den)) * 1.852
        else:
            val_km = int(val_str) * 1.852
        fr = f"{val_km:.1f} km"
        return {"raw": token, "fr": fr}, idx + 1

    return None, idx


def parse_phenomena(tokens: list, idx: int) -> tuple:
    phenomena = []
    while idx < len(tokens):
        token = tokens[idx]
        # Skip tokens starting with RE (recent weather) prefix
        check = token[2:] if token.startswith("RE") else token
        m = WX_PATTERN.match(check)
        if not m:
            break
        intensity_code = m[1] or ""
        descriptor_code = m[2] or ""
        phenom1 = m[3]
        phenom2 = m[4] or ""

        parts = []
        if intensity_code == "-":
            parts.append("légère")
        elif intensity_code == "+":
            parts.append("forte")
        elif intensity_code == "VC":
            parts.append("dans les environs :")

        if descriptor_code == "TS":
            parts.append("orage avec")
        elif descriptor_code == "SH":
            parts.append("averses de")
        elif descriptor_code == "FZ":
            parts.append("verglaçant(e)")
        elif descriptor_code and descriptor_code in WEATHER_CODES:
            parts.append(WEATHER_CODES[descriptor_code])

        parts.append(WEATHER_CODES.get(phenom1, phenom1))
        if phenom2:
            parts.append("et " + WEATHER_CODES.get(phenom2, phenom2))

        recent_prefix = "Récemment : " if token.startswith("RE") else ""

        phenomena.append({
            "raw": token,
            "fr": recent_prefix + " ".join(parts),
            "code": phenom1,
        })
        idx += 1
    return phenomena, idx


def parse_clouds(tokens: list, idx: int) -> tuple:
    clouds = []
    while idx < len(tokens):
        token = tokens[idx]
        # Vertical visibility
        if re.match(r'^VV\d{3}$', token):
            height_ft = int(token[2:]) * 100
            height_m = round(height_ft * 0.3048)
            clouds.append({
                "raw": token,
                "cover": "VV",
                "cover_fr": "visibilité verticale",
                "height_ft": height_ft,
                "height_m": height_m,
                "fr": f"visibilité verticale à {height_ft:,} ft ({height_m:,} m)".replace(",", " "),
            })
            idx += 1
            continue

        m = CLOUD_PATTERN.match(token)
        if not m:
            break
        cover = m[1]
        height_code = m[2]
        ctype = m[3] or ""

        cover_fr, _ = CLOUD_COVER.get(cover, (cover, 0))
        cloud_entry = {"raw": token, "cover": cover, "cover_fr": cover_fr}

        if height_code:
            height_ft = int(height_code) * 100
            height_m = round(height_ft * 0.3048)
            cloud_entry["height_ft"] = height_ft
            cloud_entry["height_m"] = height_m
            type_suffix = ""
            if ctype == "CB":
                type_suffix = " (cumulo-nimbus ⛈️)"
            elif ctype == "TCU":
                type_suffix = " (cumulus bourgeonnant)"
            fr = f"{cover_fr} à {height_ft:,} ft ({height_m:,} m){type_suffix}".replace(",", " ")
        else:
            fr = cover_fr

        cloud_entry["fr"] = fr
        clouds.append(cloud_entry)
        idx += 1
    return clouds, idx


def parse_temp_dewpoint(tokens: list, idx: int) -> tuple:
    if idx >= len(tokens):
        return None, None, idx
    m = re.match(r'^(M?\d{2})/(M?\d{2})$', tokens[idx])
    if not m:
        return None, None, idx

    def parse_c(s: str) -> int:
        return -int(s[1:]) if s.startswith('M') else int(s)

    return parse_c(m[1]), parse_c(m[2]), idx + 1


def parse_pressure(tokens: list, idx: int) -> tuple:
    if idx >= len(tokens):
        return None, idx
    token = tokens[idx]
    if re.match(r'^Q\d{4}$', token):
        hpa = int(token[1:])
        return {"raw": token, "hpa": hpa, "fr": f"{hpa} hPa"}, idx + 1
    if re.match(r'^A\d{4}$', token):
        inhg = int(token[1:]) / 100
        hpa = round(inhg * 33.8639)
        return {"raw": token, "inhg": inhg, "hpa": hpa, "fr": f"{hpa} hPa ({inhg:.2f} inHg)"}, idx + 1
    return None, idx


def parse_trend(tokens: list, idx: int) -> str | None:
    if idx >= len(tokens):
        return None
    first = tokens[idx]
    rest_tokens = tokens[idx + 1:] if idx + 1 < len(tokens) else []
    prefix = TREND_MAP.get(first, first)
    if rest_tokens:
        return prefix + " : " + " ".join(rest_tokens)
    return prefix


def choose_icon(result: dict) -> str:
    phenomena_codes = [p["code"] for p in result.get("phenomena", [])]
    for code in ["TS", "SN", "GR", "RA", "DZ", "FG", "BR", "HZ"]:
        if code in phenomena_codes:
            return ICON_MAP[code]
    if result.get("cavok"):
        return "☀️"
    clouds = result.get("clouds", [])
    if clouds:
        sig = max(clouds, key=lambda c: CLOUD_COVER.get(c["cover"], ("", 0))[1])
        return ICON_MAP.get(sig["cover"], "⛅")
    return "☀️"


def build_summary(result: dict) -> str:
    sentences = []

    # Phrase 1 : ciel / phénomènes
    if result.get("cavok"):
        sentences.append("CAVOK — ciel dégagé, visibilité supérieure à 10 km.")
    else:
        sky_parts = []
        if result.get("phenomena"):
            sky_parts.extend(p["fr"] for p in result["phenomena"])
        clouds = result.get("clouds", [])
        if clouds:
            sig = max(clouds, key=lambda c: CLOUD_COVER.get(c["cover"], ("", 0))[1])
            sky_parts.append(sig["fr"])
        if sky_parts:
            sentences.append("Ciel : " + ", ".join(sky_parts) + ".")
        elif result.get("visibility"):
            pass  # visibilité mentionnée en phrase 3

    # Phrase 2 : température + vent
    temp_wind = []
    if result["temperature"] is not None:
        temp_wind.append(f"Température de {result['temperature']}°C")
        if result["dewpoint"] is not None:
            temp_wind[-1] += f" (point de rosée {result['dewpoint']}°C)"
    if result.get("wind"):
        wind = result["wind"]
        if wind.get("calm"):
            temp_wind.append("vent calme")
        else:
            temp_wind.append(f"vent {wind['fr']}")
    if temp_wind:
        sentences.append(", ".join(temp_wind) + ".")

    # Phrase 3 : pression + visibilité
    pv = []
    if result.get("pressure"):
        pv.append(f"Pression de {result['pressure']['fr']}")
    if result.get("visibility") and not result.get("cavok"):
        pv.append(f"visibilité {result['visibility']['fr']}")
    if pv:
        sentences.append(", ".join(pv) + ".")

    return " ".join(sentences)


def parse_metar(raw: str) -> dict:
    result = {
        "raw": raw.strip(),
        "station": None,
        "time_utc": None,
        "auto": False,
        "wind": None,
        "visibility": None,
        "phenomena": [],
        "clouds": [],
        "temperature": None,
        "dewpoint": None,
        "pressure": None,
        "trend": None,
        "cavok": False,
        "summary": "",
        "icon": "☀️",
        "error": None,
    }

    tokens = raw.strip().split()
    if not tokens:
        result["error"] = "METAR vide."
        return result

    idx = 0

    # Préfixe optionnel METAR / SPECI
    if tokens[idx] in ("METAR", "SPECI"):
        idx += 1

    if idx >= len(tokens):
        result["error"] = "METAR incomplet."
        return result

    # Station
    result["station"] = tokens[idx].upper()
    idx += 1

    # AUTO / COR
    while idx < len(tokens) and tokens[idx] in ("AUTO", "COR"):
        result["auto"] = True
        idx += 1

    # Heure
    if idx < len(tokens) and re.match(r'^\d{6}Z$', tokens[idx]):
        result["time_utc"] = parse_time(tokens[idx])
        idx += 1

    # Vent
    wind, idx = parse_wind(tokens, idx)
    result["wind"] = wind

    # Direction variable (ex. 180V260) — sauter
    if idx < len(tokens) and re.match(r'^\d{3}V\d{3}$', tokens[idx]):
        idx += 1

    # CAVOK ou visibilité + phénomènes + nuages
    if idx < len(tokens) and tokens[idx] == "CAVOK":
        result["cavok"] = True
        result["visibility"] = {"raw": "CAVOK", "fr": "supérieure à 10 km (CAVOK)"}
        idx += 1
    else:
        vis, idx = parse_visibility(tokens, idx)
        result["visibility"] = vis

        phenomena, idx = parse_phenomena(tokens, idx)
        result["phenomena"] = phenomena

        clouds, idx = parse_clouds(tokens, idx)
        result["clouds"] = clouds

    # Température / point de rosée
    temp, dew, idx = parse_temp_dewpoint(tokens, idx)
    result["temperature"] = temp
    result["dewpoint"] = dew

    # Pression
    pressure, idx = parse_pressure(tokens, idx)
    result["pressure"] = pressure

    # Tendance (reste)
    result["trend"] = parse_trend(tokens, idx)

    # Résumé et icône
    result["icon"] = choose_icon(result)
    result["summary"] = build_summary(result)

    return result
