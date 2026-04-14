from pydantic import BaseModel


class ElectionInput(BaseModel):
    FEAT_Vote_2017: float | None = None
    Mediane_du_niveau_vie: float | None = None
    part_ouvrier: float | None = None
    part_cadre: float | None = None
    part_retraite_csp: float | None = None
    Cambriolages_de_logement_nombre_sum: float | None = None
    Violences_physiques_hors_cadre_familial_nombre_sum: float | None = None
    age_moyen: float | None = None
    Sans_Diplome_CEP: float | None = None


class ElectionPrediction(BaseModel):
    extreme_gauche: float
    gauche: float
    centre: float
    droite: float
    extreme_droite: float


class PredictionRequest(BaseModel):
    model_name: str
    input: ElectionInput


class PredictionResponse(BaseModel):
    model_name: str
    prediction: ElectionPrediction
