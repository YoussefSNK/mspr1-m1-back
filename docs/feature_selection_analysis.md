# Analyse de la sélection de features (votes par bloc, présidentielle 2022)

Ce document compare le jeu de features actuellement utilisé en production
avec le jeu proposé par l'analyse de corrélations (rapport, section 4),
vérifie la disponibilité des données dans `data/Table_FEATURES_FINAL.csv`,
et confronte les corrélations annoncées (vs candidats 2017) à celles
recalculées sur nos cibles 2022 (`data/Table_TARGETS (1).csv`, parts de vote
par bloc : `extreme_gauche`, `gauche`, `centre`, `droite`, `extreme_droite`).

Script associé : [`training/train_model.py`](../training/train_model.py).

## 1. Modèle actuel en production

`modele_rf_global_electio.pkl` (RandomForestRegressor, 100 arbres, 5 sorties)
attend 9 features (`feature_names_in_`) :

```
FEAT_Vote_2017, Mediane_du_niveau_vie, part_ouvrier, part_cadre,
part_retraite_csp, Cambriolages_de_logement_nombre_sum,
Violences_physiques_hors_cadre_familial_nombre_sum, age_moyen, Sans_Diplome_CEP
```

`FEAT_Vote_2017` n'existe dans aucun fichier de `data/` — feature
"orpheline", imputée par défaut (~15.7) à l'inférence.

## 2. Mapping du nouveau jeu de features (rapport, section 4.5)

| Variable décrite (rapport) | Colonne dataset | Disponibilité (525 communes jointes) |
|---|---|---|
| Part des revenus du patrimoine | `Part_des_revenus_du_patrimoine_et_autres_revenus` | 133/525 (25%) |
| Part des impôts | `Part_des_impots` | 133/525 (25%) |
| Part des ménages fiscaux imposés | `Part_des_menages_fiscaux_imposes` | 133/525 (25%) |
| 9e décile du niveau de vie | `9e_decile_du_niveau_de_vie_` | 133/525 (25%) |
| Rapport interdécile D9/D1 | `Rapport_interdecile_9e_decile/1er_decile` | 133/525 (25%) |
| Revenus non salariés | `dont_part_des_revenus_des_activites_non_salariees` | 133/525 (25%) |
| Niveau de vie médian | `Mediane_du_niveau_vie` | ~520/525 (99%) |
| Prestations familiales | `dont_part_des_prestations_familiales` | 133/525 (25%) |
| Indemnités de chômage | `dont_part_des_indemnites_de_chomage` | 133/525 (25%) |
| Pensions et retraites | `Part_des_pensions_retraites_et_rentes` | 133/525 (25%) |
| Âge moyen | `age_moyen` | ~520/525 (99%) |
| Part des cadres | `part_cadre` | ~520/525 (99%) |
| Part des ouvriers | `part_ouvrier` | ~520/525 (99%) |
| Taille de commune (log) | dérivée : `log(Nombre_de_personnes_dans_les_menages_fiscaux)` | ~520/525 (99%) |

**Toutes les variables existent.** Mais 10 des 14 (toute la famille
fiscalité/patrimoine/inégalités/précarité) ne sont renseignées que pour
**133 communes sur 525 (~25%)** — secret statistique INSEE (Filosofi),
publié uniquement pour les communes ≥ ~2000 habitants.

## 3. Corrélations recalculées sur 2022 vs rapport (2017)

Comparaison `corrélation rapport (vs candidat 2017)` ↔ `corrélation
recalculée (vs bloc 2022, sur les communes disponibles)`.
Correspondance approximative des blocs : Centre≈Macron,
Extrême-droite≈Le Pen/Zemmour, Droite≈LR/Pécresse-Dupont-Aignan,
Gauche≈Mélenchon & alliés.

| Variable | Rapport (2017) | Recalculé (2022) | Verdict |
|---|---|---|---|
| `Part_des_impots` | -0.79 (Macron), +0.77 (Le Pen) | **-0.91** (Centre), **+0.68** (Extrême-droite) | ✅ confirmé, encore plus fort |
| `Part_des_menages_fiscaux_imposes` | +0.77 (Macron), -0.66 (Le Pen) | **+0.79** (Centre), **-0.61** (Extrême-droite) | ✅ quasi identique |
| `9e_decile_du_niveau_de_vie_` | +0.75 (Macron), -0.73 (Le Pen) | **+0.89** (Centre), **-0.63** (Extrême-droite) | ✅ confirmé, plus fort sur Centre |
| `Mediane_du_niveau_vie` | +0.57 (Macron), -0.50 (Le Pen) | **+0.63** (Centre), **-0.49** (Extrême-droite) | ✅ quasi identique |
| `part_cadre` | +0.42 (Macron), -0.48 (Le Pen) | **+0.38** (Centre), **-0.44** (Extrême-droite) | ✅ quasi identique |
| `part_ouvrier` | +0.47 (Le Pen), -0.39 (Macron) | **+0.41** (Extrême-droite), **-0.38** (Centre) | ✅ quasi identique |
| `log_taille_commune` | +0.46 (Macron), -0.32 (Le Pen) | +0.38 (Centre), **-0.32** (Extrême-droite) ; max réel = -0.45 (Droite) | ✅ confirmé |
| `dont_part_des_prestations_familiales` | -0.62 (Macron), +0.60 (Le Pen) | **-0.77** (Centre), **+0.49** (Extrême-droite) | ✅ confirmé |
| `dont_part_des_indemnites_de_chomage` | -0.56 (Macron), +0.41 (Le Pen) | **-0.62** (Centre), **+0.34** (Extrême-droite) | ✅ confirmé |
| `age_moyen` | +0.44 (Fillon), -0.34 (Mélenchon) | +0.33 (Droite), -0.29 (Gauche) | ✅ confirmé |
| `Part_des_pensions_retraites_et_rentes` | +0.57 (Fillon), -0.52 (Mélenchon) | +0.47 (Droite), -0.38 (Gauche) | ✅ confirmé, un peu plus faible |
| `dont_part_des_revenus_des_activites_non_salariees` | +0.63 (Fillon) | +0.56 (Droite) | ✅ confirmé |
| `Part_des_revenus_du_patrimoine_et_autres_revenus` | +0.86 (Fillon), -0.57 (Mélenchon) | +0.63 (Droite/Centre), -0.51 (Extrême-gauche) | ⚠️ même sens, plus faible |
| `Rapport_interdecile_9e_decile/1er_decile` | +0.67 (Fillon), -0.53 (Le Pen) | +0.27 (Droite), -0.46 (Extrême-droite) | ⚠️ plus faible sur Droite |

### Variables actuellement en production mais écartées par le rapport

| Variable | Corrélation max recalculée (2022) |
|---|---|
| `Cambriolages_de_logement_nombre_sum` | ~0.24 |
| `Violences_physiques_hors_cadre_familial_nombre_sum` | ~0.27 |
| `Sans_Diplome_CEP` | ~0.28 |
| `part_retraite_csp` | ~0.24 |

Ces valeurs (0.2-0.3) confirment le constat du rapport : ces variables sont
peu discriminantes comparées au nouveau jeu (corrélations 0.4 à 0.9).

## 4. Comparaison des modèles entraînés (`training/train_model.py`)

Pipeline identique pour les deux jeux (`SimpleImputer(median)` →
`StandardScaler` → `RandomForestRegressor(100 arbres)`), même split
train/test (80/20, `random_state=42`), sur les 525 communes jointes.
Métriques complètes (R², MAE, RMSE par bloc + validation croisée 5-fold)
sauvegardées dans
[`training/output/metrics.json`](../training/output/metrics.json)
(régénéré à chaque exécution du script).

### Hold-out test set (20%, 105 communes)

| Bloc | Actuel (8 features) R² / MAE / RMSE | Nouveau (14 features) R² / MAE / RMSE |
|---|---|---|
| extreme_gauche | -0.068 / 0.62 / 0.98 | -0.046 / 0.62 / 0.97 |
| gauche | +0.204 / 4.28 / 5.82 | +0.278 / 4.11 / 5.54 |
| centre | +0.425 / 2.80 / 3.87 | +0.447 / 2.79 / 3.79 |
| droite | +0.255 / 2.27 / 3.30 | +0.260 / 2.18 / 3.28 |
| extreme_droite | +0.373 / 4.83 / 6.63 | +0.381 / 4.73 / 6.58 |
| **Moyenne** | **+0.238 / 2.96 / 4.12** | **+0.264 / 2.89 / 4.03** |

### Validation croisée (5-fold, R² moyen toutes sorties confondues)

| | Actuel (8 features) | Nouveau (14 features) |
|---|---|---|
| CV R² moyen ± écart-type | **+0.205 ± 0.067** | **+0.197 ± 0.054** |

Sur le hold-out, le nouveau jeu améliore légèrement et de façon homogène
toutes les sorties (R² moyen +0.238 → +0.264, MAE moyen -0.07 pt). **Mais
en validation croisée 5-fold, les deux jeux sont équivalents** (0.205 vs
0.197, écart dans le bruit) — l'amélioration observée sur le split unique
n'est donc pas significative à elle seule. `extreme_gauche` reste mal
prédit dans les deux cas (très faible variance des votes extrême-gauche
dans l'échantillon).

### Importance des features (nouveau modèle, RandomForest)

| Feature | Importance |
|---|---|
| `Mediane_du_niveau_vie` | 0.249 |
| `log_taille_commune` | 0.180 |
| `part_ouvrier` | 0.151 |
| `part_cadre` | 0.150 |
| `age_moyen` | 0.140 |
| `Part_des_impots` | 0.062 |
| `9e_decile_du_niveau_de_vie_` | 0.018 |
| `dont_part_des_indemnites_de_chomage` | 0.012 |
| `Rapport_interdecile_9e_decile/1er_decile` | 0.009 |
| `dont_part_des_revenus_des_activites_non_salariees` | 0.007 |
| `Part_des_pensions_retraites_et_rentes` | 0.007 |
| `Part_des_revenus_du_patrimoine_et_autres_revenus` | 0.006 |
| `Part_des_menages_fiscaux_imposes` | 0.005 |
| `dont_part_des_prestations_familiales` | 0.005 |

**Constat clé** : les 5 features les plus importantes (83% du poids total)
sont les 4 variables "saines" (`Mediane_du_niveau_vie`, `part_ouvrier`,
`part_cadre`, `age_moyen`) + `log_taille_commune` (dérivée, 99% disponible).
Les 6 variables fiscales détaillées (imputées à 75%) ne pèsent que 5% à
elles toutes les six — `Part_des_impots` (0.062) est la seule à apporter un
signal notable malgré l'imputation, cohérent avec sa très forte corrélation
brute (-0.91).

## 5. Limites et pistes

- **Échantillon réduit pour les variables fiscales** : seules 133/525
  communes (≥ ~2000 hab.) ont les 6 variables fiscales détaillées
  (patrimoine, impôts, ménages imposés, déciles, revenus non salariés,
  prestations/chômage/pensions). Pour les ~75% restants, ces valeurs sont
  imputées à la médiane — leur apport réel est donc dilué, ce que confirme
  l'importance des features (5% de poids cumulé pour ces 6 variables) et
  la validation croisée (gain non significatif vs le modèle actuel).
- **Le nouveau jeu de 14 features n'apporte pas de gain net démontré** en
  validation croisée. L'essentiel du signal vient de 5 variables :
  `Mediane_du_niveau_vie`, `part_ouvrier`, `part_cadre`, `age_moyen`
  (déjà dans le modèle actuel) et `log_taille_commune` (nouvelle, dérivée,
  bien disponible). `Part_des_impots` apporte un signal modeste
  supplémentaire malgré l'imputation.
- **Pistes pour aller plus loin** :
  - Un modèle "réduit" à 5 features (les 4 variables saines actuelles +
    `log_taille_commune`, en remplaçant `part_retraite_csp`,
    `Sans_Diplome_CEP` et les 2 variables de criminalité) pourrait
    égaler voire dépasser les deux jeux testés, avec moins de risque
    d'imputation.
  - Comparer un modèle entraîné uniquement sur les 133 communes complètes
    (sans imputation, avec les 14 features) vs le modèle actuel sur les
    mêmes 133 communes.
  - Tester un feature flag binaire "donnée fiscale disponible" en plus de
    l'imputation, pour laisser le modèle distinguer les deux populations.
  - `extreme_gauche` reste mal prédit (R² négatif/proche de 0) dans tous
    les scénarios — le rapport ne propose rien de spécifique pour ce bloc.
- **Si un nouveau modèle est promu en production**, il faudra mettre à jour
  `FEATURE_ORDER` dans
  [`app/services/prediction_service.py`](../app/services/prediction_service.py)
  et le schéma `ElectionInput` dans
  [`app/api/schemas/prediction.py`](../app/api/schemas/prediction.py)
  pour refléter les nouvelles features (et adapter `data_loader.py` /
  l'API de saisie pour les fournir).

## 6. Mise en œuvre (modèle 14 features en production)

Le nouveau modèle (`training/output/*_v2.pkl`) a été promu en production :

- `imputer_electio.pkl`, `scaler_electio.pkl`, `modele_rf_global_electio.pkl`
  (racine du projet) sont désormais les artefacts 14 features. Les anciens
  artefacts 9 features sont archivés dans
  [`training/archive/v1/`](../training/archive/v1/) (non chargés par
  `model_registry`, qui ne scanne que la racine).
- `FEATURE_ORDER` (`prediction_service.py`) et `ElectionInput`
  (`schemas/prediction.py`) reflètent les 14 features. Deux noms ont dû être
  adaptés pour rester des identifiants Python valides, et une feature est
  dérivée côté backend :

  | Champ `ElectionInput` (API) | Feature modèle (`feature_names_in_`) |
  |---|---|
  | `decile_9_niveau_de_vie` | `9e_decile_du_niveau_de_vie_` |
  | `rapport_interdecile_d9_d1` | `Rapport_interdecile_9e_decile/1er_decile` |
  | `nombre_personnes_menages_fiscaux` (population brute) | `log_taille_commune` (= `log(valeur)`, calculé dans `predict()`) |

  Les 11 autres champs gardent le nom exact de la feature dataset
  (`Part_des_impots`, `Mediane_du_niveau_vie`, `age_moyen`, `part_cadre`,
  `part_ouvrier`, etc.).
- Tout champ omis (`null`/absent) est imputé à la médiane par
  `imputer_electio.pkl`, comme avant — testé avec un payload partiel
  (uniquement les 5 features "saines").
- **Front-end** : le payload `POST /api/predict` (`PredictionRequest.input`)
  doit désormais envoyer ces 14 champs au lieu des 9 précédents
  (`FEAT_Vote_2017`, `part_retraite_csp`,
  `Cambriolages_de_logement_nombre_sum`,
  `Violences_physiques_hors_cadre_familial_nombre_sum`, `Sans_Diplome_CEP`
  disparaissent).
- **MinIO** : aucune action requise pour que l'app fonctionne (le bucket
  `models` n'existe pas localement → fallback automatique sur les `.pkl` de
  la racine, vérifié). Si le bucket `models` est utilisé en environnement
  partagé, y uploader les 3 nouveaux `.pkl` (mêmes noms canoniques) pour que
  ces environnements chargent aussi le modèle 14 features.
