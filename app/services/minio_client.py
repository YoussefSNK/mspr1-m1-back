from minio import Minio
from minio.error import S3Error

from app.core.config import settings


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
