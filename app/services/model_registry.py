import joblib

from app.services.minio_client import download_pkl, list_pkl_objects

_registry: dict[str, object] = {}


def load_all_models() -> None:
    pkl_objects = list_pkl_objects()
    for object_name in pkl_objects:
        local_path = download_pkl(object_name)
        model_name = object_name.removesuffix(".pkl")
        _registry[model_name] = joblib.load(local_path)


def get_model(name: str) -> object:
    if name not in _registry:
        raise KeyError(f"Modèle '{name}' introuvable. Modèles disponibles : {list(_registry.keys())}")
    return _registry[name]


def list_models() -> list[str]:
    return list(_registry.keys())
