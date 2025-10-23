import time
from sqlalchemy import create_engine
import os

def wait_for_db(url, name):
    for _ in range(30):  # retry up to ~30 times
        try:
            engine = create_engine(url)
            with engine.connect():
                print(f"{name} is ready.")
                return True
        except Exception as e:
            print(f"Waiting for {name}... ({e})")
            time.sleep(3)
    raise Exception(f"{name} not reachable after waiting.")

if __name__ == "__main__":
    source_url = os.getenv("SOURCE_DB_URL")
    warehouse_url = os.getenv("WAREHOUSE_DB_URL")

    wait_for_db(source_url, "source_db")
    wait_for_db(warehouse_url, "warehouse_db")
