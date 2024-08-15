import os
import supabase
import psycopg2

from typing import Tuple, List, Dict
from supabase import create_client, Client
from ..core.create_sql_query import create_table_query


class SupabaseClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        try:
            url: str = os.environ.get("SUPABASE_URL")
            key: str = os.environ.get("SUPABASE_KEY")
            self.supabase: Client = create_client(url, key)
            self.postgres = psycopg2.connect(dsn=os.environ.get("POSTGRES_URI"))
        except Exception as e:
            raise Exception(f"Error occured while connecting to supabase: {e}")

    def get_client(self) -> Client:
        return self.supabase

    def create_table(self, table_name: str, fields: Dict[str, str]):
        try:
            cur = self.postgres.cursor()
            cur.execute(
                create_table_query(
                    table_name=table_name,
                    columns=fields,
                )
            )
            self.postgres.commit()
            cur.close()
            self.postgres.close()
        except Exception as e:
            raise Exception(e)

    def add_bulk_data(self, table_name: str, data: List):
        try:
            response = self.supabase.table(table_name).insert(data).execute()
            return response
        except Exception as exception:
            return exception

    def create_storage_bucket(self, bucket_name: str):
        try:
            res = self.supabase.storage.create_bucket(bucket_name)
            return res
        except Exception as e:
            raise Exception(f"An error occured while creating storage bucket: {e}")

    def upload_files(self, files: List):
        responses = []
        for file in files:
            with open(os.path.join("temp", file), "rb") as f:
                resp = self.supabase.storage.from_("emails").upload(
                    file=f,
                    path=f"/{file}",
                    file_options={"content-type": "plain/text"},
                )
                responses.append(resp)

        return responses

    def list_files(self, bucket_name: str):
        res = self.supabase.storage.from_(bucket_name).list()
        return res
