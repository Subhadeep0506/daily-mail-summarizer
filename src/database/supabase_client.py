import os
from typing import List

from supabase import Client, StorageException, create_client

from ..core.logger import SingletonLogger
from ..database.database import Base, engine


class SupabaseClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        self.logger = SingletonLogger().logger
        if self._initialized:
            self.logger.info("SupabaseClient already initialized")
            return
        try:
            url: str = os.environ.get("SUPABASE_URL")
            key: str = os.environ.get("SUPABASE_SERVICE_KEY")
            self.supabase: Client = create_client(url, key)
            Base.metadata.create_all(bind=engine)
            self.logger.info("Database tables created")
            self.logger.info("SupabaseClient initialized")
        except Exception as e:
            self.logger.error(f"Error occured while connecting to supabase: {e}")

    def get_client(self) -> Client:
        return self.supabase

    def add_bulk_data(self, table_name: str, data: List):
        try:
            self.logger.info(f"Adding data to table '{table_name}'")
            response = self.supabase.table(table_name).insert(data).execute()
            self.logger.info(f"Data added to table '{table_name}'")
            return response
        except Exception as exception:
            self.logger.error(
                f"An error occured while adding data to table '{table_name}': {exception}"
            )

    def create_storage_bucket(self, bucket_name: str):
        try:
            res = self.supabase.storage.create_bucket(bucket_name)
            self.logger.info(f"Storage bucket created: {bucket_name}")
            return res
        except Exception as e:
            self.logger.error(f"An error occured while creating storage bucket: {e}")

    def upload_files(self, files: List, bucket_name: str):
        responses = []
        try:
            bucket = self.supabase.storage.get_bucket(bucket_name)
            for file in files:
                try:
                    with open(os.path.join("temp", file), "rb") as f:
                        resp = bucket.upload(
                            file=f,
                            path=f"/{file}",
                            file_options={"content-type": "application/json"},
                        )
                        responses.append(resp)
                except Exception as e:
                    self.logger.error(
                        f"An error occured while uploading file '{file}': {e}"
                    )
            self.logger.info(f"All files uploaded.")
            return responses
        except StorageException as e:
            self.logger.error(f"Bucket with name '{bucket_name}' not found: {e}")

    def list_files(self, bucket_name: str):
        try:
            bucket = self.supabase.storage.get_bucket(bucket_name)
            res = bucket.list()
            self.logger.info(f"Fetched {len(res)} files from bucket '{bucket_name}'.")
            return res
        except StorageException as e:
            self.logger.error(f"Bucket with name '{bucket_name}' not found: {e}")
        except Exception as e:
            self.logger.error(f"An error occured while listing files: {e}")

    def get_file_urls(self, bucket_name: str):
        try:
            bucket = self.supabase.storage.get_bucket(bucket_name)
            file_metadatas = self.list_files(bucket_name)
            file_urls = []
            for file in file_metadatas:
                if file["name"].endswith(".json"):
                    res = bucket.get_public_url(file["name"], options={"download": True})
                    file_urls.append({"name": file["name"], "url": res})
            self.logger.info(f"Fetched {len(res)} files from bucket '{bucket_name}'.")
            return file_urls
        except StorageException as e:
            self.logger.error(f"Bucket with name '{bucket_name}' not found: {e}")
        except Exception as e:
            self.logger.error(f"An error occured while listing files: {e}")
