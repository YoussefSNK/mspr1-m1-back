import os
import tempfile

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

MODELS_TMP_DIR = os.path.join(tempfile.gettempdir(), "mspr_models")


def get_minio_client() -> Minio:
    return Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def check_connection() -> bool:
    client = get_minio_client()
    try:
        client.bucket_exists(settings.MINIO_BUCKET_MODELS)
        return True
    except S3Error:
        return False


def list_pkl_objects() -> list[str]:
    client = get_minio_client()
    objects = client.list_objects(settings.MINIO_BUCKET_MODELS, recursive=True)
    return [obj.object_name for obj in objects if obj.object_name.endswith(".pkl")]


def download_pkl(object_name: str) -> str:
    client = get_minio_client()
    os.makedirs(MODELS_TMP_DIR, exist_ok=True)
    dest_path = os.path.join(MODELS_TMP_DIR, os.path.basename(object_name))
    client.fget_object(settings.MINIO_BUCKET_MODELS, object_name, dest_path)
    return dest_path
