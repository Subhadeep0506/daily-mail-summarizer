import os

from typing import List
from supabase import create_client, Client
from ..database.database import engine, Base
from ..core.logger import SingletonLogger


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
            key: str = os.environ.get("SUPABASE_KEY")
            self.supabase: Client = create_client(url, key)
            Base.metadata.create_all(engine)
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

    def upload_files(self, files: List):
        responses = []
        for file in files:
            try:
                with open(os.path.join("temp", file), "rb") as f:
                    resp = self.supabase.storage.from_("emails").upload(
                        file=f,
                        path=f"/{file}",
                        file_options={"content-type": "plain/text"},
                    )
                    responses.append(resp)
            except Exception as e:
                self.logger.error(
                    f"An error occured while uploading file '{file}': {e}"
                )
        self.logger.info(f"All files uploaded.")
        return responses

    def list_files(self, bucket_name: str):
        try:
            res = self.supabase.storage.from_(bucket_name).list()
            return res
        except Exception as e:
            self.logger.error(f"An error occured while listing files: {e}")
