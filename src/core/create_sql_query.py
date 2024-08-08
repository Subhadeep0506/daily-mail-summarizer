from typing import List, Dict


def create_table_query(table_name, columns: List[Dict[str, str]]):
    query = f"""CREATE TABLE IF NOT EXISTS public.{table_name} ("""
    for i, column in enumerate(columns):
        _temp = f'{column["col_name"]} {column["type"]} {column["role"] if column["role"] != "None" else ""}'
        if i < len(columns) - 1:
            query += _temp + ","
        else:
            query += _temp

    query += ");"
    return query
