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

import psycopg

BASE_DIR = Path(__file__).resolve().parent

ROADMAP_FILE = BASE_DIR/"db"/"seed"/"roadmap.json"

def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "dsa_agent"),
        user=os.getenv("POSTGRES_USER", "dsa_user"),
        password=os.getenv("POSTGRES_PASSWORD", "dsa_password"),
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
    topic_id = cur.fetchone()[0]
    for child in node.get("children", []):
        insert_node(
            cur,
            child,
            parent_id=topic_id
        )
        
def main():
    print("Loading roadmap....")
    with open(ROADMAP_FILE, "r", encoding="uft-8") as file:
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

    