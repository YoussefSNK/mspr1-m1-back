import glob
import os
import joblib

from app.services.minio_client import download_pkl, list_pkl_objects

_registry: dict[str, object] = {}

# Répertoire racine du projet (deux niveaux au-dessus de ce fichier)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_from_local() -> None:
    """Charge les .pkl présents à la racine du projet."""
    pkl_files = glob.glob(os.path.join(_PROJECT_ROOT, "*.pkl"))
    for path in pkl_files:
        model_name = os.path.basename(path).removesuffix(".pkl")
        _registry[model_name] = joblib.load(path)
        print(f"[model_registry] Chargé localement : {model_name}")


def load_all_models() -> None:
    try:
        pkl_objects = list_pkl_objects()
        for object_name in pkl_objects:
            local_path = download_pkl(object_name)
            model_name = object_name.removesuffix(".pkl")
            _registry[model_name] = joblib.load(local_path)
            print(f"[model_registry] Chargé depuis MinIO : {model_name}")
    except Exception as e:
        print(f"[model_registry] MinIO indisponible ({e}), chargement local…")
        _load_from_local()


def get_model(name: str) -> object:
    if name not in _registry:
        raise KeyError(f"Modèle '{name}' introuvable. Modèles disponibles : {list(_registry.keys())}")
    return _registry[name]


def list_models() -> list[str]:
    return list(_registry.keys())
