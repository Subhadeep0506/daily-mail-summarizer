from typing import List, Dict
from ..schema.types import types


def create_table_query(table_name, columns: Dict[str, str]):
    query = f"""CREATE TABLE IF NOT EXISTS public.{table_name} ("""
    for i, column in enumerate(columns):
        _temp = f'{column["col_name"]} {column["type"]}'
        if i < len(columns) - 1:
            query += _temp + ","
        else:
            query += _temp

    query += ");"
    return query
