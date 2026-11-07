import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path("data/instamart.db")
SQL_PATH = Path("sql/queries.sql")

# Read SQL query
sql_text = SQL_PATH.read_text(encoding="utf-8")

# Execute each SQL statement using pandas
queries = [
    query.strip()
    for query in sql_text.split(";")
    if query.strip()
]

with sqlite3.connect(DB_PATH) as connection:

    for index, query in enumerate(queries, start=1):
        result = pd.read_sql_query(query, connection)

        print(f"\n========== Q{index} RESULTS ==========")
        print(result.to_string(index=False))
        print(f"\nTotal rows returned: {len(result)}")