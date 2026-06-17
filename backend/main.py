"""
main.py — FastAPI application for Spot On!
"""

import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import data_service
import model as prediction_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Spot On! API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static league list
# ---------------------------------------------------------------------------

LEAGUES = [
    # --- Ligas de clubes ---
    {"id": "PL",  "name": "Premier League",         "country": "England",       "type": "club"},
    {"id": "BL1", "name": "Bundesliga",              "country": "Germany",       "type": "club"},
    {"id": "SA",  "name": "Serie A",                 "country": "Italy",         "type": "club"},
    {"id": "PD",  "name": "La Liga",                 "country": "Spain",         "type": "club"},
    {"id": "FL1", "name": "Ligue 1",                 "country": "France",        "type": "club"},
    {"id": "BSB", "name": "Brasileirão Série A",     "country": "Brazil",        "type": "club"},

    # --- Seleções nacionais ---
    {"id": "WC",  "name": "Copa do Mundo FIFA",      "country": "Internacional", "type": "national"},
    {"id": "EC",  "name": "Eurocopa UEFA",            "country": "Europa",        "type": "national"},
    {"id": "CA",  "name": "Copa América CONMEBOL",   "country": "Américas",      "type": "national"},
    {"id": "CAN", "name": "Copa Africana das Nações","country": "África",        "type": "national"},
    {"id": "WCQ", "name": "Eliminatórias Copa do Mundo","country": "Internacional","type": "national"},
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/leagues")
def get_leagues():
    return LEAGUES


@app.get("/api/teams")
def get_teams(league: str = Query(..., description="League ID, e.g. PL")):
    logger.info("GET /api/teams  league=%s", league)
    teams = data_service.get_teams(league)
    if not teams:
        raise HTTPException(status_code=404, detail="No teams found for this league.")
    return teams


class PredictRequest(BaseModel):
    home_team_id: int
    away_team_id: int
    league_id: str


@app.post("/api/predict")
def predict(req: PredictRequest):
    logger.info(
        "POST /api/predict  home=%s away=%s league=%s",
        req.home_team_id, req.away_team_id, req.league_id,
    )

    if req.home_team_id == req.away_team_id:
        raise HTTPException(status_code=400, detail="Os dois times devem ser diferentes.")

    # Resolve team names
    teams = data_service.get_teams(req.league_id)
    team_map = {t["id"]: t["name"] for t in teams}

    home_name = team_map.get(req.home_team_id)
    away_name = team_map.get(req.away_team_id)

    if not home_name:
        raise HTTPException(status_code=404, detail=f"Time mandante (id={req.home_team_id}) não encontrado.")
    if not away_name:
        raise HTTPException(status_code=404, detail=f"Time visitante (id={req.away_team_id}) não encontrado.")

    try:
        result = prediction_model.predict(
            home_team_id=req.home_team_id,
            away_team_id=req.away_team_id,
            league_id=req.league_id,
            home_team_name=home_name,
            away_team_name=away_name,
        )
    except Exception as exc:
        logger.exception("Error in prediction: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao calcular previsão. Verifique os logs.")

    return result
