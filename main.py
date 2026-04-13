from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from data_loader import TENDENCY_LABELS, load_all

# ---------------------------------------------------------------------------
# État global chargé au démarrage
# ---------------------------------------------------------------------------

_cities: list[dict] = []
_cities_by_id: dict[int, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cities, _cities_by_id
    print("[startup] Chargement des données…")
    _cities = load_all(departement="33")
    _cities_by_id = {c["id"]: c for c in _cities}
    print(f"[startup] {len(_cities)} communes chargées.")
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="MSPR Elections API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)


# ---------------------------------------------------------------------------
# Schémas Pydantic
# ---------------------------------------------------------------------------


class FilterBody(BaseModel):
    unemploymentRate: Optional[float] = None
    crimeRate: Optional[float] = None
    averageAge: Optional[float] = None
    educationLevel: Optional[str] = None  # "low" | "medium" | "high"
    averageSalary: Optional[float] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ZONE_TO_DEPT: dict[str, str] = {
    "gironde": "33",
}


def _city_summary(c: dict) -> dict:
    """Champs renvoyés dans /api/cities (liste)."""
    return {
        "id": c["id"],
        "name": c["name"],
        "lon": c["lon"],
        "lat": c["lat"],
        "population": c["population"],
        "participation": c["participation"],
        "tendance": c["tendance"],
    }


def _within(value: float, target: float, tolerance_pct: float = 25.0) -> bool:
    """Vérifie si value est dans ±tolerance_pct% de target."""
    if target == 0:
        return value == 0
    return abs(value - target) / abs(target) <= tolerance_pct / 100


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
def root():
    return {"message": "ok"}


# 1. Indicateurs globaux par zone ----------------------------------------

@app.get("/api/results")
def get_results(zone: str = Query(..., description="Ex: gironde")):
    dept = _ZONE_TO_DEPT.get(zone.lower())
    if dept is None:
        raise HTTPException(
            status_code=404,
            detail=f"Zone inconnue : '{zone}'. Zones disponibles : {list(_ZONE_TO_DEPT)}",
        )

    total_inscrits = 0.0
    total_abstentions = 0.0
    total_exprimes = 0.0
    cumul_votes: dict[str, float] = {k: 0.0 for k in TENDENCY_LABELS}

    for c in _cities:
        total_inscrits += c["_inscrits"]
        total_abstentions += c["_abstentions"]
        total_exprimes += c["_exprimes"]
        for k, v in c["_votes_raw"].items():
            cumul_votes[k] += v

    participation = (
        (total_inscrits - total_abstentions) / total_inscrits * 100
        if total_inscrits > 0
        else 0.0
    )

    tendances = [
        {
            "key": k,
            "label": TENDENCY_LABELS[k],
            "value": round(cumul_votes[k] / total_exprimes * 100, 1)
            if total_exprimes > 0
            else 0.0,
        }
        for k in ["extreme-gauche", "gauche", "centre", "droite", "extreme-droite"]
    ]

    return {
        "zone": zone.capitalize(),
        "totalVoters": int(total_inscrits),
        "participation": round(participation, 1),
        "tendances": tendances,
    }


# 2. Liste des villes (markers carte) ------------------------------------

@app.get("/api/cities")
def get_cities(departement: str = Query("33")):
    if departement != "33":
        raise HTTPException(
            status_code=404,
            detail=f"Département '{departement}' non disponible. Seul le 33 (Gironde) est supporté.",
        )
    return [_city_summary(c) for c in _cities]


# 3. Filtre socio-économique ---------------------------------------------

@app.post("/api/cities/filter")
def filter_cities(body: FilterBody):
    results = []
    for c in _cities:
        socio = c["socioEconomique"]

        if body.educationLevel is not None:
            if socio["educationLevel"] != body.educationLevel:
                continue

        if body.unemploymentRate is not None:
            if not _within(socio["unemploymentRate"], body.unemploymentRate):
                continue

        if body.crimeRate is not None:
            if not _within(socio["crimeRate"], body.crimeRate):
                continue

        if body.averageAge is not None:
            if not _within(socio["averageAge"], body.averageAge):
                continue

        if body.averageSalary is not None:
            if not _within(socio["averageSalary"], body.averageSalary):
                continue

        results.append(_city_summary(c))

    return results


# 4. Fiche détaillée d'une ville -----------------------------------------

@app.get("/api/cities/{city_id}")
def get_city(city_id: int):
    city = _cities_by_id.get(city_id)
    if city is None:
        raise HTTPException(status_code=404, detail=f"Ville id={city_id} introuvable")

    return {
        "id": city["id"],
        "name": city["name"],
        "population": city["population"],
        "participation": city["participation"],
        "tendance": city["tendance"],
        "socioEconomique": city["socioEconomique"],
        "resultats": city["resultats"],
    }


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
