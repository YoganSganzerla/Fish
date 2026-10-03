# database/query_database.py

from database.influx_client import client
import pandas as pd

def query_database(sql_query: str):

    try:

        result = client.query_dataframe(sql_query)

        return result

    except Exception as e:

        print(f"Erro ao consultar banco: {e}")
        return pd.DataFrame()