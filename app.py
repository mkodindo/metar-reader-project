import re
import requests
from flask import Flask, render_template, request, jsonify
from metar_parser import parse_metar

app = Flask(__name__)

METAR_API = "https://aviationweather.gov/api/data/metar?ids={code}&format=raw&taf=false&hours=1"
ICAO_RE = re.compile(r'^[A-Z]{4}$')


def validate_icao(code: str) -> str | None:
    code = code.strip().upper()
    return code if ICAO_RE.match(code) else None


def fetch_metar(icao: str) -> tuple:
    url = METAR_API.format(code=icao)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        text = resp.text.strip()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            return None, f"Aucun METAR disponible pour le code {icao}. Vérifiez que le code est correct."
        return lines[0], None
    except requests.exceptions.Timeout:
        return None, "La requête a expiré (délai dépassé). Vérifiez votre connexion internet."
    except requests.exceptions.ConnectionError:
        return None, "Impossible de se connecter au serveur météo. Vérifiez votre connexion internet."
    except requests.exceptions.HTTPError as e:
        return None, f"Erreur du serveur météo (HTTP {e.response.status_code})."
    except Exception as e:
        return None, f"Erreur inattendue : {str(e)}"


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    icao_input = ""

    if request.method == "POST":
        icao_input = request.form.get("icao", "").strip()
        icao = validate_icao(icao_input)

        if not icao:
            error = "Code ICAO invalide. Saisissez exactement 4 lettres (ex. LFPO, KJFK, EGLL)."
        else:
            raw_metar, fetch_error = fetch_metar(icao)
            if fetch_error:
                error = fetch_error
            else:
                try:
                    result = parse_metar(raw_metar)
                    if result.get("error"):
                        error = result["error"]
                        result = None
                except Exception as e:
                    error = f"Erreur lors du décodage du METAR : {str(e)}"

    return render_template(
        "index.html",
        result=result,
        error=error,
        icao_input=icao_input.upper(),
    )


@app.route("/api/metar/<code>", methods=["GET"])
def api_metar(code: str):
    icao = validate_icao(code)
    if not icao:
        return jsonify({"error": "Code ICAO invalide."}), 400

    raw_metar, fetch_error = fetch_metar(icao)
    if fetch_error:
        return jsonify({"error": fetch_error}), 502

    try:
        result = parse_metar(raw_metar)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Erreur de décodage : {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
