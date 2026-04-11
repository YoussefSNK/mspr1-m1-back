from prometheus_client import Counter, Histogram

PREDICTIONS_TOTAL = Counter(
    "predictions_total",
    "Nombre total de prédictions effectuées",
    ["model_name", "status"],
)

PREDICTION_LATENCY = Histogram(
    "prediction_latency_seconds",
    "Durée d'une prédiction en secondes",
    ["model_name"],
)
