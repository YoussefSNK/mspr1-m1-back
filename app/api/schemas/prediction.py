from pydantic import BaseModel


class ElectionInput(BaseModel):
    Part_des_revenus_du_patrimoine_et_autres_revenus: float | None = None
    Part_des_impots: float | None = None
    Part_des_menages_fiscaux_imposes: float | None = None
    decile_9_niveau_de_vie: float | None = None
    rapport_interdecile_d9_d1: float | None = None
    dont_part_des_revenus_des_activites_non_salariees: float | None = None
    Mediane_du_niveau_vie: float | None = None
    dont_part_des_prestations_familiales: float | None = None
    dont_part_des_indemnites_de_chomage: float | None = None
    Part_des_pensions_retraites_et_rentes: float | None = None
    age_moyen: float | None = None
    part_cadre: float | None = None
    part_ouvrier: float | None = None
    nombre_personnes_menages_fiscaux: float | None = None


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
