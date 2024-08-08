import os
import supabase
import psycopg2

from typing import Tuple
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

    def create_table(self, table_name: str, config):
        try:
            cur = self.postgres.cursor()
            cur.execute(
                create_table_query(
                    table_name=table_name,
                    columns=config["database"][table_name]["columns"],
                )
            )
            self.postgres.commit()
            cur.close()
            self.postgres.close()
        except Exception as e:
            raise Exception(e)

    def add_email(self):
        pass
