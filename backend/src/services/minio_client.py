from minio import Minio
from core.config import config


class MinioClient():
    def __init__(self):
        minio_client = Minio(
            config.minio_endpoint,
            access_key=config.minio_access_key,
            secret_key=config.minio_secret_key,
            secure=config.secure
        )
        self.client = minio_client

    def initialize_bucket(self, bucket_name):
        try:
            # Check if bucket exists
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                print("Bucket created.")
            else:
                print("Bucket already exists.")
        except Exception as e:
            print(f"Error initializing MinIO: {e}")

    def upload_file(self, bucket_name: str, object_name: str, file_data):
        self.client.put_object(
            bucket_name,
            object_name,
            file_data,
            length=-1,
            part_size=10*1024*1024
        )

    def get_file_url(self, bucket_name: str, object_name: str) -> str:
        return self.client.presigned_get_object(bucket_name, object_name)