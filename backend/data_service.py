"""
data_service.py — Football-data.org integration + SQLite cache
"""

import os
import json
import time
import sqlite3
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")

# IDs de competições de seleções nacionais (sem vantagem de campo)
NATIONAL_COMPETITIONS = {"WC", "EC", "CA", "CAN", "WCQ", "UCL", "UEL", "EUCL"}
BASE_URL = "https://api.football-data.org/v4"
DB_PATH = os.path.join(os.path.dirname(__file__), "cache.db")

# ---------------------------------------------------------------------------
# Mock data — used when no API key is configured
# ---------------------------------------------------------------------------

MOCK_TEAMS: dict[str, list[dict]] = {
    "PL": [
        {"id": 57,  "name": "Arsenal"},
        {"id": 58,  "name": "Aston Villa"},
        {"id": 61,  "name": "Chelsea"},
        {"id": 62,  "name": "Everton"},
        {"id": 63,  "name": "Fulham"},
        {"id": 64,  "name": "Liverpool"},
        {"id": 65,  "name": "Manchester City"},
        {"id": 66,  "name": "Manchester United"},
        {"id": 67,  "name": "Newcastle United"},
        {"id": 73,  "name": "Tottenham Hotspur"},
        {"id": 354, "name": "Crystal Palace"},
        {"id": 356, "name": "Leicester City"},
        {"id": 397, "name": "Brighton & Hove Albion"},
        {"id": 402, "name": "Brentford"},
        {"id": 563, "name": "West Ham United"},
        {"id": 715, "name": "Bournemouth"},
        {"id": 745, "name": "Wolverhampton Wanderers"},
        {"id": 1044,"name": "Nottingham Forest"},
        {"id": 328, "name": "Burnley"},
        {"id": 341, "name": "Luton Town"},
    ],
    "BL1": [
        {"id": 5,   "name": "Bayern München"},
        {"id": 4,   "name": "Borussia Dortmund"},
        {"id": 3,   "name": "Bayer 04 Leverkusen"},
        {"id": 721, "name": "RB Leipzig"},
        {"id": 18,  "name": "Borussia Mönchengladbach"},
        {"id": 6,   "name": "Eintracht Frankfurt"},
        {"id": 7,   "name": "VfL Wolfsburg"},
        {"id": 10,  "name": "Hamburger SV"},
        {"id": 11,  "name": "VfB Stuttgart"},
        {"id": 12,  "name": "SC Freiburg"},
        {"id": 13,  "name": "FC Augsburg"},
        {"id": 14,  "name": "Werder Bremen"},
        {"id": 15,  "name": "FC Köln"},
        {"id": 16,  "name": "1. FC Union Berlin"},
        {"id": 17,  "name": "1. FSV Mainz 05"},
        {"id": 19,  "name": "Hertha BSC"},
        {"id": 23,  "name": "Hoffenheim"},
        {"id": 24,  "name": "FC Heidenheim"},
    ],
    "SA": [
        {"id": 98,  "name": "AC Milan"},
        {"id": 99,  "name": "Internazionale"},
        {"id": 100, "name": "Juventus"},
        {"id": 102, "name": "Napoli"},
        {"id": 103, "name": "AS Roma"},
        {"id": 104, "name": "Lazio"},
        {"id": 105, "name": "Atalanta"},
        {"id": 107, "name": "Fiorentina"},
        {"id": 108, "name": "Torino"},
        {"id": 110, "name": "SS Lazio"},
        {"id": 113, "name": "Bologna"},
        {"id": 115, "name": "Udinese"},
        {"id": 116, "name": "Sassuolo"},
        {"id": 118, "name": "Cagliari"},
        {"id": 119, "name": "Genoa"},
        {"id": 470, "name": "Frosinone"},
        {"id": 471, "name": "Hellas Verona"},
        {"id": 472, "name": "Monza"},
        {"id": 586, "name": "Empoli"},
        {"id": 445, "name": "Salernitana"},
    ],
    "PD": [
        {"id": 77,  "name": "Athletic Club"},
        {"id": 78,  "name": "Atlético de Madrid"},
        {"id": 79,  "name": "CA Osasuna"},
        {"id": 80,  "name": "Celta de Vigo"},
        {"id": 81,  "name": "FC Barcelona"},
        {"id": 82,  "name": "Getafe CF"},
        {"id": 83,  "name": "Girona FC"},
        {"id": 84,  "name": "Granada CF"},
        {"id": 85,  "name": "Mallorca"},
        {"id": 86,  "name": "Real Betis"},
        {"id": 87,  "name": "Real Madrid"},
        {"id": 88,  "name": "Real Sociedad"},
        {"id": 89,  "name": "Rayo Vallecano"},
        {"id": 90,  "name": "Sevilla FC"},
        {"id": 92,  "name": "Valencia CF"},
        {"id": 250, "name": "Deportivo Alavés"},
        {"id": 95,  "name": "Villarreal CF"},
        {"id": 96,  "name": "UD Las Palmas"},
        {"id": 264, "name": "Cádiz CF"},
        {"id": 745, "name": "UD Almería"},
    ],
    "FL1": [
        {"id": 516, "name": "Paris Saint-Germain"},
        {"id": 517, "name": "AS Monaco"},
        {"id": 518, "name": "Olympique de Marseille"},
        {"id": 519, "name": "Olympique Lyonnais"},
        {"id": 521, "name": "Lille OSC"},
        {"id": 522, "name": "RC Lens"},
        {"id": 523, "name": "OGC Nice"},
        {"id": 524, "name": "Stade Rennais FC"},
        {"id": 525, "name": "RC Strasbourg"},
        {"id": 527, "name": "Toulouse FC"},
        {"id": 528, "name": "Stade de Reims"},
        {"id": 529, "name": "Montpellier HSC"},
        {"id": 530, "name": "FC Metz"},
        {"id": 532, "name": "Clermont Foot 63"},
        {"id": 533, "name": "FC Lorient"},
        {"id": 534, "name": "Stade Brestois"},
        {"id": 546, "name": "Le Havre AC"},
        {"id": 548, "name": "Nantes"},
    ],
    "BSB": [
        {"id": 1765,"name": "Atlético Mineiro"},
        {"id": 1773,"name": "Flamengo"},
        {"id": 1783,"name": "Palmeiras"},
        {"id": 1769,"name": "Grêmio"},
        {"id": 1767,"name": "Internacional"},
        {"id": 1768,"name": "Cruzeiro"},
        {"id": 1770,"name": "Botafogo"},
        {"id": 1771,"name": "Fluminense"},
        {"id": 1772,"name": "Vasco da Gama"},
        {"id": 1774,"name": "Santos"},
        {"id": 1776,"name": "São Paulo"},
        {"id": 1777,"name": "Corinthians"},
        {"id": 1778,"name": "Sport Club do Recife"},
        {"id": 1779,"name": "Bahia"},
        {"id": 1780,"name": "Athletico Paranaense"},
        {"id": 1781,"name": "Fortaleza EC"},
        {"id": 1782,"name": "RB Bragantino"},
        {"id": 1784,"name": "América Mineiro"},
        {"id": 1785,"name": "Cuiabá EC"},
        {"id": 1786,"name": "EC Goiás"},
    ],

    # -----------------------------------------------------------------------
    # Seleções nacionais — IDs da football-data.org
    # -----------------------------------------------------------------------

    # Copa do Mundo / Eliminatórias (competições abertas ao tier gratuito)
    "WC": [
        {"id": 759,  "name": "🇧🇷 Brasil"},
        {"id": 760,  "name": "🇦🇷 Argentina"},
        {"id": 762,  "name": "🇫🇷 França"},
        {"id": 764,  "name": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra"},
        {"id": 765,  "name": "🇩🇪 Alemanha"},
        {"id": 766,  "name": "🇪🇸 Espanha"},
        {"id": 768,  "name": "🇵🇹 Portugal"},
        {"id": 769,  "name": "🇳🇱 Holanda"},
        {"id": 770,  "name": "🇧🇪 Bélgica"},
        {"id": 771,  "name": "🇺🇾 Uruguai"},
        {"id": 772,  "name": "🇨🇴 Colômbia"},
        {"id": 773,  "name": "🇨🇱 Chile"},
        {"id": 780,  "name": "🇮🇹 Itália"},
        {"id": 781,  "name": "🇲🇽 México"},
        {"id": 782,  "name": "🇺🇸 Estados Unidos"},
        {"id": 784,  "name": "🇯🇵 Japão"},
        {"id": 785,  "name": "🇰🇷 Coreia do Sul"},
        {"id": 788,  "name": "🇸🇳 Senegal"},
        {"id": 789,  "name": "🇲🇦 Marrocos"},
        {"id": 791,  "name": "🇨🇷 Costa Rica"},
        {"id": 793,  "name": "🇪🇨 Equador"},
        {"id": 794,  "name": "🇵🇪 Peru"},
        {"id": 795,  "name": "🇵🇦 Panamá"},
        {"id": 796,  "name": "🇧🇴 Bolívia"},
        {"id": 799,  "name": "🏴󠁧󠁢󠁷󠁬󠁳󠁿 País de Gales"},
        {"id": 800,  "name": "🇦🇺 Austrália"},
        {"id": 801,  "name": "🇨🇦 Canadá"},
        {"id": 805,  "name": "🇨🇭 Suíça"},
        {"id": 806,  "name": "🇩🇰 Dinamarca"},
        {"id": 807,  "name": "🇸🇪 Suécia"},
        {"id": 808,  "name": "🇳🇴 Noruega"},
        {"id": 809,  "name": "🇵🇱 Polônia"},
    ],

    # Eurocopa — mesmo plantel da WC (seleções europeias)
    "EC": [
        {"id": 764,  "name": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra"},
        {"id": 765,  "name": "🇩🇪 Alemanha"},
        {"id": 766,  "name": "🇪🇸 Espanha"},
        {"id": 768,  "name": "🇵🇹 Portugal"},
        {"id": 769,  "name": "🇳🇱 Holanda"},
        {"id": 770,  "name": "🇧🇪 Bélgica"},
        {"id": 780,  "name": "🇮🇹 Itália"},
        {"id": 762,  "name": "🇫🇷 França"},
        {"id": 799,  "name": "🏴󠁧󠁢󠁷󠁬󠁳󠁿 País de Gales"},
        {"id": 805,  "name": "🇨🇭 Suíça"},
        {"id": 806,  "name": "🇩🇰 Dinamarca"},
        {"id": 807,  "name": "🇸🇪 Suécia"},
        {"id": 808,  "name": "🇳🇴 Noruega"},
        {"id": 809,  "name": "🇵🇱 Polônia"},
        {"id": 811,  "name": "🇦🇹 Áustria"},
        {"id": 812,  "name": "🇷🇴 Romênia"},
        {"id": 813,  "name": "🇨🇿 República Tcheca"},
        {"id": 814,  "name": "🇭🇺 Hungria"},
        {"id": 815,  "name": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escócia"},
        {"id": 816,  "name": "🇹🇷 Turquia"},
        {"id": 817,  "name": "🇸🇰 Eslováquia"},
        {"id": 818,  "name": "🇸🇮 Eslovênia"},
        {"id": 820,  "name": "🇬🇷 Grécia"},
        {"id": 821,  "name": "🇷🇸 Sérvia"},
        {"id": 822,  "name": "🇭🇷 Croácia"},
    ],

    # Copa América — seleções sul-americanas
    "CA": [
        {"id": 759,  "name": "🇧🇷 Brasil"},
        {"id": 760,  "name": "🇦🇷 Argentina"},
        {"id": 771,  "name": "🇺🇾 Uruguai"},
        {"id": 772,  "name": "🇨🇴 Colômbia"},
        {"id": 773,  "name": "🇨🇱 Chile"},
        {"id": 793,  "name": "🇪🇨 Equador"},
        {"id": 794,  "name": "🇵🇪 Peru"},
        {"id": 796,  "name": "🇧🇴 Bolívia"},
        {"id": 798,  "name": "🇻🇪 Venezuela"},
        {"id": 797,  "name": "🇵🇾 Paraguai"},
        {"id": 782,  "name": "🇺🇸 Estados Unidos"},
        {"id": 781,  "name": "🇲🇽 México"},
        {"id": 791,  "name": "🇨🇷 Costa Rica"},
        {"id": 795,  "name": "🇵🇦 Panamá"},
    ],

    # Copa Africana das Nações
    "CAN": [
        {"id": 788,  "name": "🇸🇳 Senegal"},
        {"id": 789,  "name": "🇲🇦 Marrocos"},
        {"id": 790,  "name": "🇿🇦 África do Sul"},
        {"id": 792,  "name": "🇳🇬 Nigéria"},
        {"id": 825,  "name": "🇬🇭 Gana"},
        {"id": 826,  "name": "🇨🇮 Costa do Marfim"},
        {"id": 827,  "name": "🇪🇬 Egito"},
        {"id": 828,  "name": "🇲🇱 Mali"},
        {"id": 829,  "name": "🇨🇲 Camarões"},
        {"id": 830,  "name": "🇦🇴 Angola"},
        {"id": 831,  "name": "🇹🇳 Tunísia"},
        {"id": 832,  "name": "🇩🇿 Argélia"},
        {"id": 833,  "name": "🇿🇲 Zâmbia"},
        {"id": 834,  "name": "🇿🇼 Zimbábue"},
        {"id": 835,  "name": "🇲🇿 Moçambique"},
        {"id": 836,  "name": "🇧🇫 Burkina Faso"},
    ],

    # Eliminatórias da Copa do Mundo (todas seleções)
    "WCQ": [
        {"id": 759,  "name": "🇧🇷 Brasil"},
        {"id": 760,  "name": "🇦🇷 Argentina"},
        {"id": 762,  "name": "🇫🇷 França"},
        {"id": 764,  "name": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra"},
        {"id": 765,  "name": "🇩🇪 Alemanha"},
        {"id": 766,  "name": "🇪🇸 Espanha"},
        {"id": 768,  "name": "🇵🇹 Portugal"},
        {"id": 769,  "name": "🇳🇱 Holanda"},
        {"id": 770,  "name": "🇧🇪 Bélgica"},
        {"id": 771,  "name": "🇺🇾 Uruguai"},
        {"id": 772,  "name": "🇨🇴 Colômbia"},
        {"id": 773,  "name": "🇨🇱 Chile"},
        {"id": 780,  "name": "🇮🇹 Itália"},
        {"id": 781,  "name": "🇲🇽 México"},
        {"id": 782,  "name": "🇺🇸 Estados Unidos"},
        {"id": 784,  "name": "🇯🇵 Japão"},
        {"id": 785,  "name": "🇰🇷 Coreia do Sul"},
        {"id": 788,  "name": "🇸🇳 Senegal"},
        {"id": 789,  "name": "🇲🇦 Marrocos"},
        {"id": 793,  "name": "🇪🇨 Equador"},
        {"id": 794,  "name": "🇵🇪 Peru"},
        {"id": 796,  "name": "🇧🇴 Bolívia"},
        {"id": 797,  "name": "🇵🇾 Paraguai"},
        {"id": 798,  "name": "🇻🇪 Venezuela"},
        {"id": 801,  "name": "🇨🇦 Canadá"},
        {"id": 805,  "name": "🇨🇭 Suíça"},
        {"id": 806,  "name": "🇩🇰 Dinamarca"},
        {"id": 807,  "name": "🇸🇪 Suécia"},
        {"id": 808,  "name": "🇳🇴 Noruega"},
        {"id": 809,  "name": "🇵🇱 Polônia"},
        {"id": 822,  "name": "🇭🇷 Croácia"},
        {"id": 800,  "name": "🇦🇺 Austrália"},
    ],
}

# Curated quality ratings per national team (0.0 = weak, 1.0 = elite).
# Based roughly on FIFA rankings. Used only for mock data generation.
TEAM_QUALITY: dict[int, float] = {
    # Top tier (World Cup contenders)
    760: 0.95,  # Argentina (World Champion)
    762: 0.93,  # France
    766: 0.92,  # Spain
    768: 0.90,  # Portugal
    765: 0.88,  # Germany
    759: 0.87,  # Brazil
    770: 0.86,  # Belgium
    769: 0.85,  # Netherlands
    780: 0.84,  # Italy
    764: 0.83,  # England
    822: 0.80,  # Croatia
    788: 0.75,  # Senegal
    805: 0.74,  # Switzerland
    806: 0.73,  # Denmark
    809: 0.72,  # Poland
    807: 0.71,  # Sweden
    771: 0.78,  # Uruguay
    772: 0.76,  # Colombia
    773: 0.70,  # Chile
    793: 0.68,  # Ecuador
    784: 0.74,  # Japan
    785: 0.72,  # South Korea
    789: 0.76,  # Morocco
    782: 0.73,  # USA
    801: 0.69,  # Canada
    781: 0.70,  # Mexico
    808: 0.70,  # Norway
    800: 0.67,  # Australia
    816: 0.70,  # Turkey
    815: 0.68,  # Scotland
    811: 0.69,  # Austria
    812: 0.65,  # Romania
    813: 0.66,  # Czech Republic
    814: 0.65,  # Hungary
    817: 0.64,  # Slovakia
    818: 0.63,  # Slovenia
    821: 0.67,  # Serbia
    820: 0.62,  # Greece
    799: 0.66,  # Wales
    794: 0.65,  # Peru
    796: 0.55,  # Bolivia
    797: 0.63,  # Paraguay
    798: 0.62,  # Venezuela
    791: 0.61,  # Costa Rica
    795: 0.58,  # Panama
    # African teams
    792: 0.72,  # Nigeria
    825: 0.68,  # Ghana
    826: 0.74,  # Ivory Coast
    827: 0.70,  # Egypt
    828: 0.67,  # Mali
    829: 0.67,  # Cameroon
    831: 0.66,  # Tunisia
    832: 0.67,  # Algeria
    790: 0.65,  # South Africa
    830: 0.58,  # Angola
    833: 0.57,  # Zambia
    836: 0.59,  # Burkina Faso
}


def _generate_mock_matches(team_id: int, league_id: str) -> list[dict]:
    """
    Generate pseudo-realistic match history for a team.
    Uses a curated quality table for national teams; falls back to a
    deterministic quality derived from team_id for club teams.
    """
    import random
    import math
    rng = random.Random(team_id * 31 + hash(league_id) % 997)

    def poisson_sample(mu: float) -> int:
        """Simple Poisson sample via Knuth algorithm."""
        if mu <= 0:
            return 0
        L = math.exp(-mu)
        p, k = 1.0, 0
        while p > L:
            p *= rng.random()
            k += 1
        return k - 1

    # Look up quality from table, or derive from team_id for clubs
    if team_id in TEAM_QUALITY:
        quality = TEAM_QUALITY[team_id]
    else:
        # For club teams: use (team_id % 100) / 100 for a wider, sane spread
        quality = 0.35 + ((team_id * 17 + 53) % 100) / 100.0 * 0.55  # 0.35 – 0.90

    # Expected goals rates
    att_mu  = 0.5 + quality * 2.2   # 0.50 – 2.70 goals/match scored
    def_mu  = 2.5 - quality * 1.8   # 0.70 – 2.50 goals/match conceded

    is_national = league_id in NATIONAL_COMPETITIONS

    matches = []
    for _ in range(38):
        if is_national:
            scored   = poisson_sample(att_mu)
            conceded = poisson_sample(def_mu)
            matches.append({"scored": scored, "conceded": conceded, "is_home": False})
        else:
            is_home = rng.random() > 0.5
            home_boost = 0.25  # typical home advantage
            if is_home:
                sc = poisson_sample(att_mu * (1 + home_boost))
                co = poisson_sample(def_mu * (1 - home_boost * 0.5))
            else:
                sc = poisson_sample(att_mu)
                co = poisson_sample(def_mu)
            matches.append({"scored": sc, "conceded": co, "is_home": is_home})
    return matches


# ---------------------------------------------------------------------------
# SQLite cache helpers
# ---------------------------------------------------------------------------

def _init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cache "
        "(key TEXT PRIMARY KEY, value TEXT, expires_at INTEGER)"
    )
    conn.commit()
    return conn


def _cache_get(key: str) -> dict | list | None:
    conn = _init_db()
    row = conn.execute(
        "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    if row and int(time.time()) < row[1]:
        return json.loads(row[0])
    return None


def _cache_set(key: str, value: dict | list, ttl_seconds: int) -> None:
    conn = _init_db()
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
        (key, json.dumps(value), int(time.time()) + ttl_seconds),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _api_get(path: str) -> dict | None:
    if not API_KEY:
        return None
    url = f"{BASE_URL}{path}"
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers={"X-Auth-Token": API_KEY})
        logger.info("football-data.org %s → %s", path, resp.status_code)
        if resp.status_code == 429:
            logger.warning("Rate limit hit on %s", path)
            return {"error": "rate_limit"}
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        logger.error("HTTP error fetching %s: %s", path, exc)
        return None


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def get_teams(league_id: str) -> list[dict]:
    """Return list of {id, name} dicts for the given league."""
    cache_key = f"teams:{league_id}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    if not API_KEY:
        teams = MOCK_TEAMS.get(league_id, [])
        _cache_set(cache_key, teams, 86400)
        return teams

    data = _api_get(f"/competitions/{league_id}/teams")
    if data is None or "error" in (data or {}):
        teams = MOCK_TEAMS.get(league_id, [])
        _cache_set(cache_key, teams, 86400)
        return teams

    teams = [
        {"id": t["id"], "name": t["name"]}
        for t in data.get("teams", [])
    ]
    _cache_set(cache_key, teams, 86400)
    return teams


def _parse_matches(data: dict, team_id: int, is_national: bool) -> list[dict]:
    """Parse raw API match list. Each record has explicit 'scored'/'conceded' fields."""
    matches = []
    for m in data.get("matches", []):
        score = m.get("score", {}).get("fullTime", {})
        home_id = m.get("homeTeam", {}).get("id")
        hg = score.get("home")
        ag = score.get("away")
        if hg is None or ag is None:
            continue
        is_home = False if is_national else (home_id == team_id)
        scored   = int(hg) if is_home else int(ag)
        conceded = int(ag) if is_home else int(hg)
        matches.append({
            "scored":     scored,
            "conceded":   conceded,
            "is_home":    is_home,
        })
    return matches


def get_team_matches(team_id: int, league_id: str, limit: int = 38) -> list[dict]:
    """
    Return parsed match history for a team.

    Strategy for national teams (free tier often restricts competition filters):
      1. Try with competition filter (e.g. WC,EC,CA,CAN,WCQ)
      2. If that returns 0 matches, retry without competition filter (all recent matches)
      3. If still 0 or API fails entirely, fall back to deterministic mock data

    For club competitions:
      Try with competition filter → fallback to mock if 0 or error.
    """
    cache_key = f"matches:{team_id}:{league_id}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    if not API_KEY:
        matches = _generate_mock_matches(team_id, league_id)
        _cache_set(cache_key, matches, 21600)
        return matches

    is_national = league_id in NATIONAL_COMPETITIONS
    matches: list[dict] = []

    if is_national:
        # Attempt 1: filter by all national competitions
        national_ids = ",".join(NATIONAL_COMPETITIONS - {"UCL", "UEL", "EUCL"})
        data = _api_get(
            f"/teams/{team_id}/matches"
            f"?competitions={national_ids}&status=FINISHED&limit={limit}"
        )
        if data and "error" not in data:
            matches = _parse_matches(data, team_id, is_national)

        # Attempt 2: if still empty, try without competition filter (broader search)
        if not matches:
            logger.info(
                "National team %s: no matches with competition filter, trying without filter", team_id
            )
            data = _api_get(
                f"/teams/{team_id}/matches"
                f"?status=FINISHED&limit={limit}"
            )
            if data and "error" not in data:
                matches = _parse_matches(data, team_id, is_national)

    else:
        data = _api_get(
            f"/teams/{team_id}/matches"
            f"?competitions={league_id}&status=FINISHED&limit={limit}"
        )
        if data and "error" not in data:
            matches = _parse_matches(data, team_id, is_national)

    # ---- Final fallback: if API gave us nothing useful, use mock data ----
    if not matches:
        logger.warning(
            "No valid matches from API for team %s in %s — using mock data", team_id, league_id
        )
        matches = _generate_mock_matches(team_id, league_id)

    _cache_set(cache_key, matches, 21600)
    return matches


def compute_team_stats(team_id: int, league_id: str) -> dict:
    """
    Returns attack/defence factors split by home and away.
    For national teams, all matches are treated as neutral-venue:
    scored/conceded averages are computed across all matches regardless of
    side, and both home_ and away_ factors are set to the same neutral value.
    """
    matches = get_team_matches(team_id, league_id)

    def safe_avg(values: list[float]) -> float:
        return sum(values) / len(values) if values else 1.0

    is_national = league_id in NATIONAL_COMPETITIONS

    if is_national:
        # All neutral-venue: use explicit scored/conceded fields
        scored   = safe_avg([m["scored"]   for m in matches])
        conceded = safe_avg([m["conceded"] for m in matches])
        return {
            "home_scored":  scored,
            "home_concede": conceded,
            "away_scored":  scored,
            "away_concede": conceded,
            "matches_used": len(matches),
        }

    home_matches = [m for m in matches if m["is_home"]]
    away_matches = [m for m in matches if not m["is_home"]]

    home_scored  = safe_avg([m["scored"]   for m in home_matches])
    home_concede = safe_avg([m["conceded"] for m in home_matches])
    away_scored  = safe_avg([m["scored"]   for m in away_matches])
    away_concede = safe_avg([m["conceded"] for m in away_matches])

    return {
        "home_scored":  home_scored,
        "home_concede": home_concede,
        "away_scored":  away_scored,
        "away_concede": away_concede,
        "matches_used": len(matches),
    }
