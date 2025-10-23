import os
import pandas as pd
from sqlalchemy import create_engine

SOURCE_DB_URL = "postgresql://postgres:postgres@source_db:5432/source_db"

def load_csv_to_postgres(csv_path, table_name, engine):
    print(f"Loading {table_name} from {csv_path}...")
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print(f"Loaded {len(df)} records into {table_name}.")

def main():
    print("Connecting to source database...")
    engine = create_engine(SOURCE_DB_URL)

    csv_files = {
        "listings_data": "/data/listings_data.csv",
        "monthly_airbnb_data": "/data/monthly_airbnb_data.csv",
        "tourism_data": "/data/tourism_data.csv",
        "weather_data": "/data/weather_data.csv"
    }

    for table_name, csv_path in csv_files.items():
        if os.path.exists(csv_path):
            load_csv_to_postgres(csv_path, table_name, engine)
        else:
            print(f"Warning: {csv_path} not found. Skipping {table_name}.")

    print("All CSVs loaded successfully.")

if __name__ == "__main__":
    main()