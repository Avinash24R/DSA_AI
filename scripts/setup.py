'''
Read json

connent PostgresSql

Insert parent

get parent ID

Insert children using parent ID

recursively continue
'''

import json
import os
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv
from psycopg.rows import dict_row
import psycopg

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ROADMAP_FILE = BASE_DIR/"db"/"seed"/"roadmap.json"

def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB", "DSA_agent"),
        user=os.getenv("POSTGRES_USER", "coolUser"),
        password=os.getenv("POSTGRES_PASSWORD", "coolUserPassword"),
        row_factory=cast(Any, dict_row),
    )
def insert_node(cur , node, parent_id=None):
    cur.execute(
            """
            INSERT INTO roadmap_topics (
                parent_id,
                name,
                node_type,
                sequence_order
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (parent_id, name)
            DO UPDATE SET
                node_type = EXCLUDED.node_type,
                sequence_order = EXCLUDED.sequence_order
            RETURNING id;
            """,(
                parent_id, 
                node["name"] , 
                node["node_type"] , 
                node.get("sequence_order", 0),
            )
        )
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Insert returned no row for node {node.get('name')!r}")
    if hasattr(row, "keys"):
        topic_id = row["id"]
    else:
        topic_id = row[0]
    for child in node.get("children", []):
        insert_node(
            cur,
            child,
            parent_id=topic_id
        )
        
def main():
    print("Loading roadmap....")
    with open(ROADMAP_FILE, "r", encoding="utf-8") as file:
        roadmap = json.load(file)
    with get_connection() as conn:
        with conn.cursor() as cur:
            for node in roadmap.get("children" , []):
                insert_node(
                    cur,
                    node
                )
        conn.commit()
    print("Roadmap seeded successfully. ")
if __name__ == "__main__":
    main()
    
    