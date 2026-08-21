from minio import Minio
from minio.error import S3Error
from app.config import settings
import io

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = "langid-docs"
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created MinIO bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"MinIO Initialization Error: {e}")

    def upload_document(self, object_name: str, data: bytes, content_type: str = "application/pdf"):
        """Uploads a document to MinIO."""
        try:
            length = len(data)
            self.client.put_object(
                self.bucket_name,
                object_name,
                io.BytesIO(data),
                length=length,
                content_type=content_type
            )
            return True
        except S3Error as e:
            print(f"Error uploading to MinIO: {e}")
            return False

    def get_presigned_url(self, object_name: str, expiry_seconds: int = 3600) -> str:
        """Generates a temporary URL to download/view the document."""
        from datetime import timedelta
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expiry_seconds)
            )
            return url
        except S3Error as e:
            print(f"Error generating presigned URL: {e}")
            return ""

    def delete_document(self, object_name: str):
        """Deletes a document from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting from MinIO: {e}")
            return False

storage_service = StorageService()
