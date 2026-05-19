# ✈️ Lecteur METAR

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![Licence](https://img.shields.io/badge/licence-MIT-lightgrey)

> Application web Flask qui traduit les bulletins météo aéronautiques (METAR) en français clair et lisible.

---

## Aperçu

Les METAR sont des bulletins météo standardisés utilisés en aviation. Leur format codifié est peu lisible pour le grand public :

```
METAR LFPO 191200Z 18010KT 9999 BKN060 21/13 Q1015 NOSIG
```

Le **Lecteur METAR** transforme ce code en langage naturel :

> Ciel : ciel couvert à 6 000 ft (1 829 m). Température de 21°C (point de rosée 13°C), vent 10 nœuds vers le Sud. Pression de 1015 hPa, visibilité supérieure à 10 km. Tendance : Aucun changement significatif prévu.

---

## Fonctionnalités

- Saisie d'un code ICAO (LFPO, KJFK, EGLL…) et récupération en temps réel
- Décodage complet du METAR :
  - **Vent** — direction en français, vitesse, rafales
  - **Visibilité** — en km ou mètres, gestion CAVOK
  - **Nuages** — couverture et altitude en ft / mètres
  - **Phénomènes météo** — pluie, neige, brouillard, orage, grêle…
  - **Température et point de rosée**
  - **Pression** — hPa (Europe) et inHg (format US)
  - **Tendance** — NOSIG, BECMG, TEMPO
- Résumé en 2–3 phrases en français
- Icône météo automatique (☀️ ⛅ ☁️ 🌧️ ❄️ ⛈️ 🌫️)
- Compatibilité formats européen et américain
- Interface dark-mode responsive (aucune dépendance CSS externe)
- API JSON disponible

---

## Prérequis

- Python 3.10 ou supérieur
- `pip`

---

## Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/<votre-utilisateur>/Metar-reader.git
cd Metar-reader

# 2. Créer et activer l'environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

---

## Lancement

```bash
flask --app app run
```

Ouvrir **http://127.0.0.1:5000** dans le navigateur.

Pour activer le mode debug (rechargement automatique) :

```bash
flask --app app run --debug
```

---

## Utilisation

1. Saisir un code ICAO dans le champ de recherche (4 lettres)
2. Cliquer sur **Décoder** ou appuyer sur **Entrée**
3. Consulter le résumé et les champs décodés

Exemples de codes :

| Code | Aéroport |
|------|----------|
| `LFPO` | Paris-Orly |
| `LFPG` | Paris-Charles de Gaulle |
| `LSGG` | Genève |
| `EBBR` | Bruxelles |
| `KJFK` | New York JFK |
| `EGLL` | Londres Heathrow |

---

## API JSON

L'application expose un endpoint REST pour une utilisation programmatique.

### Requête

```
GET /api/metar/<code>
```

### Exemple

```bash
curl http://127.0.0.1:5000/api/metar/LFPO
```

### Réponse (200 OK)

```json
{
  "station": "LFPO",
  "raw": "METAR LFPO 191200Z 18010KT 9999 BKN060 21/13 Q1015 NOSIG",
  "time_utc": { "day": 19, "hour": 12, "minute": 0, "fr": "le 19 à 12h00 UTC" },
  "wind": { "fr": "10 nœuds vers le Sud", "speed": 10, "direction_fr": "Sud" },
  "visibility": { "fr": "supérieure à 10 km", "meters": 9999 },
  "clouds": [{ "fr": "ciel couvert à 6 000 ft (1 829 m)", "cover": "BKN" }],
  "temperature": 21,
  "dewpoint": 13,
  "pressure": { "fr": "1015 hPa", "hpa": 1015 },
  "trend": "Aucun changement significatif prévu",
  "icon": "⛅",
  "summary": "Ciel : ciel couvert à 6 000 ft (1 829 m). Température de 21°C, vent 10 nœuds vers le Sud. Pression de 1015 hPa."
}
```

### Codes d'erreur

| Code HTTP | Cause |
|-----------|-------|
| `400` | Code ICAO invalide (pas 4 lettres) |
| `502` | METAR introuvable ou serveur indisponible |
| `500` | Erreur de décodage interne |

---

## Structure du projet

```
Metar-reader/
├── app.py              # Application Flask (routes, validation, récupération)
├── metar_parser.py     # Décodeur METAR complet
├── requirements.txt    # Dépendances Python
└── templates/
    └── index.html      # Interface web (dark-mode, CSS embarqué)
```

---

## Source des données

Les bulletins METAR sont fournis en temps réel par l'**Aviation Weather Center**
du National Weather Service (NWS/NOAA) via l'API publique :
`https://aviationweather.gov/api/data/metar`

---

## Licence

Ce projet est distribué sous licence [MIT](https://opensource.org/licenses/MIT).
