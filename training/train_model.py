"""
Entrainement du modele de prediction des votes par bloc politique (2022)
a partir des indicateurs socio-economiques par commune.

Compare le jeu de features actuellement en production avec le nouveau jeu
issu de l'analyse de correlations (cf. docs/feature_selection_analysis.md),
puis sauvegarde les artefacts (imputer / scaler / modele) du nouveau modele
dans training/output/.

Usage:
    python training/train_model.py
"""
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn import set_config
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Conserve les noms de colonnes a travers les etapes du pipeline, pour que
# l'imputer/scaler/modele sauvegardes aient chacun un feature_names_in_ correct.
set_config(transform_output="pandas")
warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

BLOCS = ["Extreme_Gauche", "Gauche", "Centre", "Droite", "Extreme_Droite"]
OUTPUT_LABELS = ["extreme_gauche", "gauche", "centre", "droite", "extreme_droite"]

# Features actuellement utilisees en production (FEAT_Vote_2017 exclu : absent du dataset)
CURRENT_FEATURES = [
    "Mediane_du_niveau_vie",
    "part_ouvrier",
    "part_cadre",
    "part_retraite_csp",
    "Cambriolages_de_logement_nombre_sum",
    "Violences_physiques_hors_cadre_familial_nombre_sum",
    "age_moyen",
    "Sans_Diplome_CEP",
]

# Nouveau jeu de features propose par l'analyse de correlations (rapport, section 4.5)
NEW_FEATURES = [
    "Part_des_revenus_du_patrimoine_et_autres_revenus",
    "Part_des_impots",
    "Part_des_menages_fiscaux_imposes",
    "9e_decile_du_niveau_de_vie_",
    "Rapport_interdecile_9e_decile/1er_decile",
    "dont_part_des_revenus_des_activites_non_salariees",
    "Mediane_du_niveau_vie",
    "dont_part_des_prestations_familiales",
    "dont_part_des_indemnites_de_chomage",
    "Part_des_pensions_retraites_et_rentes",
    "age_moyen",
    "part_cadre",
    "part_ouvrier",
    "log_taille_commune",
]


def _to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", ".").str.strip(), errors="coerce")


def _normalize_code(code) -> str:
    try:
        return str(int(float(code)))
    except (ValueError, TypeError):
        return str(code).strip()


def load_dataset() -> pd.DataFrame:
    feat = pd.read_csv(DATA_DIR / "Table_FEATURES_FINAL.csv")
    targ = pd.read_csv(DATA_DIR / "Table_TARGETS (1).csv")

    feat["Code_commune"] = feat["Code_commune"].apply(_normalize_code)
    targ["Code_commune"] = targ["Code_commune"].apply(_normalize_code)
    feat = feat.drop_duplicates(subset="Code_commune")
    targ = targ.drop_duplicates(subset="Code_commune")

    df = feat.merge(targ, on="Code_commune", how="inner")

    numeric_cols = set(CURRENT_FEATURES + NEW_FEATURES) - {"log_taille_commune"}
    numeric_cols |= {f"Votes_{b}" for b in BLOCS} | {"Exprimes_22", "Nombre_de_personnes_dans_les_menages_fiscaux"}
    for col in numeric_cols:
        df[col] = _to_num(df[col])

    df["log_taille_commune"] = np.log(df["Nombre_de_personnes_dans_les_menages_fiscaux"].replace(0, np.nan))
    for bloc, label in zip(BLOCS, OUTPUT_LABELS):
        df[label] = df[f"Votes_{bloc}"] / df["Exprimes_22"] * 100

    return df.dropna(subset=OUTPUT_LABELS).copy()


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("model", RandomForestRegressor(n_estimators=100, random_state=42)),
    ])


def evaluate(name, features, X, y, X_train, X_test, y_train, y_test):
    pipeline = build_pipeline()
    pipeline.fit(X_train[features], y_train)
    preds = pipeline.predict(X_test[features])

    r2 = r2_score(y_test, preds, multioutput="raw_values")
    mae = mean_absolute_error(y_test, preds, multioutput="raw_values")
    rmse = root_mean_squared_error(y_test, preds, multioutput="raw_values")

    cv = cross_val_score(
        build_pipeline(), X[features], y,
        cv=KFold(n_splits=5, shuffle=True, random_state=42), scoring="r2",
    )

    print(f"\n=== {name} ({len(features)} features) ===")
    for label, r2_val, mae_val, rmse_val in zip(OUTPUT_LABELS, r2, mae, rmse):
        print(f"  {label:18s} R2={r2_val:+.3f}  MAE={mae_val:5.2f} pts  RMSE={rmse_val:5.2f} pts")
    print(f"  {'MOYENNE':18s} R2={r2.mean():+.3f}  MAE={mae.mean():5.2f} pts  RMSE={rmse.mean():5.2f} pts")
    print(f"  CV R2 (5-fold)   : {cv.mean():+.3f} +/- {cv.std():.3f}")

    return {
        "n_features": len(features),
        "test_r2": {**{label: float(v) for label, v in zip(OUTPUT_LABELS, r2)}, "mean": float(r2.mean())},
        "test_mae": {**{label: float(v) for label, v in zip(OUTPUT_LABELS, mae)}, "mean": float(mae.mean())},
        "test_rmse": {**{label: float(v) for label, v in zip(OUTPUT_LABELS, rmse)}, "mean": float(rmse.mean())},
        "cv_r2_mean": float(cv.mean()),
        "cv_r2_std": float(cv.std()),
    }


def main():
    df = load_dataset()
    print(f"Dataset : {len(df)} communes (apres jointure features+targets et nettoyage)")

    X = df
    y = df[OUTPUT_LABELS]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    metrics_current = evaluate(
        "Modele actuel (production, 8 features)", CURRENT_FEATURES, X, y, X_train, X_test, y_train, y_test
    )
    metrics_new = evaluate(
        "Nouveau modele (analyse correlations, 14 features)", NEW_FEATURES, X, y, X_train, X_test, y_train, y_test
    )

    # Reentrainement final sur l'ensemble du dataset, pour la sauvegarde des artefacts
    final_pipeline = build_pipeline()
    final_pipeline.fit(X[NEW_FEATURES], y)

    importances = final_pipeline.named_steps["model"].feature_importances_
    feature_importances = dict(
        sorted(zip(NEW_FEATURES, importances.tolist()), key=lambda item: item[1], reverse=True)
    )

    print("\n=== Importance des features (nouveau modele, sur l'ensemble du dataset) ===")
    for feature, importance in feature_importances.items():
        print(f"  {feature:55s} {importance:.3f}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_pipeline.named_steps["imputer"], OUTPUT_DIR / "imputer_election_v2.pkl")
    joblib.dump(final_pipeline.named_steps["scaler"], OUTPUT_DIR / "scaler_election_v2.pkl")
    joblib.dump(final_pipeline.named_steps["model"], OUTPUT_DIR / "modele_rf_global_election_v2.pkl")

    with open(OUTPUT_DIR / "feature_order.json", "w", encoding="utf-8") as f:
        json.dump({"features": NEW_FEATURES, "outputs": OUTPUT_LABELS}, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "dataset_size": len(df),
            "current_features": metrics_current,
            "new_features": metrics_new,
            "new_model_feature_importances": feature_importances,
        }, f, ensure_ascii=False, indent=2)

    print(f"\nArtefacts sauvegardes dans {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
