# Migration front-end : formulaire de prédiction (9 → 14 features)

Le modèle de prédiction (`modele_rf_global_electio`) attend désormais
**14 champs** au lieu de 9. Voir [`feature_selection_analysis.md`](feature_selection_analysis.md)
pour le détail de l'analyse.

## Endpoints (inchangés)

- `GET /api/models` → liste des modèles disponibles (utiliser
  `"modele_rf_global_electio"` comme `model_name`).
- `POST /api/predict` :

```json
{
  "model_name": "modele_rf_global_electio",
  "input": { ...14 champs ci-dessous... }
}
```

Réponse (inchangée) :

```json
{
  "model_name": "modele_rf_global_electio",
  "prediction": {
    "extreme_gauche": 1.3,
    "gauche": 28.5,
    "centre": 23.3,
    "droite": 9.96,
    "extreme_droite": 36.95
  }
}
```

## Champs supprimés du formulaire

Ces 5 champs n'existent plus dans `input` :

- `FEAT_Vote_2017`
- `part_retraite_csp`
- `Cambriolages_de_logement_nombre_sum`
- `Violences_physiques_hors_cadre_familial_nombre_sum`
- `Sans_Diplome_CEP`

## Nouveaux champs (14)

Tous les champs sont **optionnels / nullable**. Un champ absent ou `null`
est automatiquement imputé par le backend avec la **médiane** observée sur
le jeu d'entraînement (525 communes) — ne pas envoyer `0` pour signifier
"valeur inconnue", car `0` est une valeur valide pour certains champs
(`part_cadre`, `part_ouvrier`).

| Champ JSON | Libellé | Unité | Min / Médiane / Max (observés) |
|---|---|---|---|
| `Part_des_revenus_du_patrimoine_et_autres_revenus` | Part des revenus du patrimoine et autres revenus | % | 3.9 / 7.1 / 22.2 |
| `Part_des_impots` | Part des impôts | % (valeur **négative**) | -22.4 / -14.6 / -9.2 |
| `Part_des_menages_fiscaux_imposes` | Part des ménages fiscaux imposés | % | 23.0 / 54.0 / 72.0 |
| `decile_9_niveau_de_vie` | 9e décile du niveau de vie | €/an | 25 950 / 36 240 / 57 800 |
| `rapport_interdecile_d9_d1` | Rapport interdécile (D9/D1) | ratio | 2.2 / 2.7 / 4.4 |
| `dont_part_des_revenus_des_activites_non_salariees` | Part des revenus d'activités non salariées | % | 1.6 / 4.2 / 9.4 |
| `Mediane_du_niveau_vie` | Niveau de vie médian | €/an | 13 940 / 21 800 / 30 500 |
| `dont_part_des_prestations_familiales` | Part des prestations familiales | % | 0.5 / 2.0 / 4.7 |
| `dont_part_des_indemnites_de_chomage` | Part des indemnités de chômage | % | 2.2 / 3.4 / 5.2 |
| `Part_des_pensions_retraites_et_rentes` | Part des pensions, retraites et rentes | % | 15.3 / 26.5 / 58.8 |
| `age_moyen` | Âge moyen de la population | années | 33.8 / 42.8 / 58.8 |
| `part_cadre` | Part de cadres | % | 0.0 / 5.0 / 33.3 |
| `part_ouvrier` | Part d'ouvriers | % | 0.0 / 15.0 / 42.9 |
| `nombre_personnes_menages_fiscaux` | Taille de la commune (nb de personnes) | nb personnes | 98 / 798 / 230 777 |

`Mediane_du_niveau_vie`, `age_moyen`, `part_cadre`, `part_ouvrier` étaient
déjà présents dans l'ancien formulaire (mêmes noms).

## Points d'attention

1. **`nombre_personnes_menages_fiscaux` = valeur brute, pas un log.**
   Le backend calcule `log(valeur)` en interne (la feature attendue par le
   modèle est `log_taille_commune`). Le front doit envoyer la population
   brute de la commune (ex: `798`), pas un logarithme.

2. **Deux noms ont été adaptés** pour rester des identifiants valides
   (le nom original contenait des caractères interdits) :
   - `decile_9_niveau_de_vie` ↔ feature modèle `9e_decile_du_niveau_de_vie_`
   - `rapport_interdecile_d9_d1` ↔ feature modèle `Rapport_interdecile_9e_decile/1er_decile`

   Ce mapping est géré côté backend (`prediction_service.py`), le front
   utilise simplement les noms JSON ci-dessus.

3. **`Part_des_impots` est négatif** dans le jeu de données (il représente
   une part déduite du revenu disponible). Ne pas appliquer de validation
   "valeur positive uniquement" sur ce champ.

4. **Disponibilité des données** : 10 des 14 champs (tout sauf
   `Mediane_du_niveau_vie`, `age_moyen`, `part_cadre`, `part_ouvrier`,
   `nombre_personnes_menages_fiscaux`) ne sont renseignés, dans le jeu de
   données source, que pour les communes de **2000+ habitants** environ
   (secret statistique INSEE). Si le formulaire est pré-rempli à partir de
   données par commune, il est normal que ces 10 champs soient souvent vides
   pour les petites communes — laisser l'utilisateur les compléter
   manuellement ou les laisser vides (imputation médiane automatique).

5. **Aucun changement nécessaire côté MinIO** ni sur les autres endpoints
   (`/api/cities*`, `/api/results`) : ils utilisent un jeu de données et de
   champs différents, non liés à `/api/predict`.
