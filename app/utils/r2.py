import boto3

from app.config import settings


class R2Client:
    def __init__(self):
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY,
            aws_secret_access_key=settings.R2_SECRET_KEY,
        )

    def upload_file(self, file_data: bytes, content_type: str, key: str) -> str:
        self._client.put_object(
            Bucket=settings.R2_BUCKET,
            Key=key,
            Body=file_data,
            ContentType=content_type,
        )
        return f"{settings.R2_PUBLIC_URL}/{key}"

    def delete_file(self, key: str) -> None:
        self._client.delete_object(Bucket=settings.R2_BUCKET, Key=key)


_r2_client: R2Client | None = None


def get_r2_client() -> R2Client:
    global _r2_client
    if _r2_client is None:
        _r2_client = R2Client()
    return _r2_client
