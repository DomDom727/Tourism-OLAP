import os
import time
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

SLEEP_BETWEEN_RETRIES = 3
MAX_RETRIES = 20
DATA_DIR = "/data"

SRC_TABLES = {
    "listings_data": "listings_data.csv",
    "monthly_airbnb_data": "monthly_airbnb_data.csv",
    "tourism_data": "tourism_data.csv",
    "weather_data": "weather_data.csv",
}

def wait_for_db(engine_url, name="database"):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            eng = create_engine(engine_url)
            conn = eng.connect()
            conn.close()
            eng.dispose()
            print(f"{name} is available: {engine_url}")
            return True
        except OperationalError:
            retries += 1
            print(f"Waiting for {name} ({retries}/{MAX_RETRIES})... sleeping {SLEEP_BETWEEN_RETRIES}s")
            time.sleep(SLEEP_BETWEEN_RETRIES)
    print(f"Timeout waiting for {name}")
    return False

def load_csvs_to_source(src_engine):
    # Read CSVs from /data and write to source_db (replace)
    for tbl, fname in SRC_TABLES.items():
        path = os.path.join(DATA_DIR, fname)
        if not os.path.isfile(path):
            print(f"CSV not found, skipping: {path}")
            continue
        print(f"📥 Loading {path} -> source_db.{tbl}")
        df = pd.read_csv(path)
        # Ensure column names are SQL-friendly
        df.columns = [c.strip() for c in df.columns]
        df.to_sql(tbl, src_engine, if_exists="replace", index=False, method="multi", chunksize=5000)
        print(f"Loaded {len(df):,} rows into {tbl}")

def build_country_dim(listings_df, monthly_df, tourism_df, weather_df):
    # derive unique countries from all sources to maximize coverage
    countries = pd.concat([
        listings_df['country'].dropna().astype(str),
        monthly_df['country'].dropna().astype(str),
        tourism_df['country'].dropna().astype(str),
        weather_df['country'].dropna().astype(str)
    ], axis=0).drop_duplicates().reset_index(drop=True).rename("country_name")
    countries = countries.to_frame()
    countries['country_name'] = countries['country_name'].str.strip()
    countries = countries[countries['country_name'] != ""].reset_index(drop=True)
    countries['country_id'] = countries.index + 1
    return countries[['country_id', 'country_name']]

def build_date_dim(monthly_df):
    # monthly_df expected to have a 'date' column in 'YYYY-MM' or full date format
    s = pd.to_datetime(monthly_df['date'], errors='coerce', format=None)
    # If strings were 'YYYY-MM', pandas returns first day of month
    s = s.dt.to_period('M').dropna().unique()
    periods = pd.Series(s).sort_values()
    df = periods.to_frame(name='period')
    df['date_actual'] = df['period'].dt.to_timestamp()
    df['year'] = df['date_actual'].dt.year
    df['month'] = df['date_actual'].dt.month
    df['day'] = df['date_actual'].dt.day
    df = df.reset_index(drop=True)
    df['date_id'] = df.index + 1
    return df[['date_id', 'date_actual', 'year', 'month', 'day']]

def upsert_dataframe(df, table_name, engine, if_exists="append"):
    # simple wrapper to write to warehouse
    df.to_sql(table_name, engine, if_exists=if_exists, index=False, method="multi", chunksize=5000)
    print(f"Upserted {len(df):,} rows into warehouse.{table_name}")

def transform_and_load(src_engine, wh_engine):
    # Extract staging tables
    listings = pd.read_sql("SELECT * FROM listings_data", src_engine) if table_exists(src_engine, 'listings_data') else pd.DataFrame()
    monthly = pd.read_sql("SELECT * FROM monthly_airbnb_data", src_engine) if table_exists(src_engine, 'monthly_airbnb_data') else pd.DataFrame()
    tourism = pd.read_sql("SELECT * FROM tourism_data", src_engine) if table_exists(src_engine, 'tourism_data') else pd.DataFrame()
    weather = pd.read_sql("SELECT * FROM weather_data", src_engine) if table_exists(src_engine, 'weather_data') else pd.DataFrame()

    # Basic cleaning - strip strings
    for df in [listings, monthly, tourism, weather]:
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Build country dim and load to warehouse.country (replace)
    countries_df = build_country_dim(listings, monthly, tourism, weather)
    if not countries_df.empty:
        # clear and write
        with wh_engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE country RESTART IDENTITY CASCADE;"))
        upsert_dataframe(countries_df, "country", wh_engine, if_exists="append")
    else:
        print("No countries found to load.")

    # Build date dim from monthly and load to warehouse.date (replace)
    if not monthly.empty:
        d_date = build_date_dim(monthly)
        if not d_date.empty:
            with wh_engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE \"date\" RESTART IDENTITY CASCADE;"))
            upsert_dataframe(d_date, "date", wh_engine, if_exists="append")
        else:
            print("No valid monthly date periods found.")
    else:
        print("monthly_airbnb_data table empty; skipping date dim build.")

    # Map country_id back to datasets using warehouse country table
    country_map = pd.read_sql("SELECT country_id, country_name FROM country", wh_engine)
    if not country_map.empty:
        # normalize key for merge
        country_map['country_name'] = country_map['country_name'].astype(str).str.strip()
        def map_country(df):
            if 'country' in df.columns:
                df['country'] = df['country'].astype(str).str.strip()
                return df.merge(country_map, left_on='country', right_on='country_name', how='left')
            else:
                df['country_id'] = None
                return df
        listings = map_country(listings)
        monthly = map_country(monthly)
        tourism = map_country(tourism)
        weather = map_country(weather)
    else:
        print("country_map is empty; country_id mapping will not occur.")

    # Load airbnb_listing (warehouse) - transform columns and types
    if not listings.empty:
        # rename and type conversions matching your warehouse schema
        listings_wn = listings.rename(columns={
            'listing_id': 'listing_id',
            'listing_name': 'listing_name',
            'city': 'city',
            'listing_type': 'listing_type',
            'room_type': 'room_type',
            'currency': 'currency_code',
            'guests': 'guest_count',
            'bedrooms': 'bedroom_count',
            'cancellation_policy': 'cancellation_policy',
            'rating_overall': 'rating_overall',
            'ttm_revenue': 'ttm_revenue',
            'ttm_avg_rate': 'ttm_avg_rate'
        })
        # ensure listing_id numeric where possible
        listings_wn['listing_id'] = pd.to_numeric(listings_wn['listing_id'], errors='coerce').astype('Int64')
        # fill missing numeric with nulls, strip whitespace
        listings_wn['city'] = listings_wn['city'].astype(str).str.strip()
        # map country_id column created earlier after merge (if present)
        if 'country_id' in listings_wn.columns:
            # cast to int
            listings_wn['country_id'] = pd.to_numeric(listings_wn['country_id'], errors='coerce').astype('Int64')
        # Keep only columns required by warehouse schema
        cols = ['listing_id','listing_name','city','country_id','listing_type','room_type',
                'currency_code','guest_count','bedroom_count','cancellation_policy',
                'rating_overall','ttm_revenue','ttm_avg_rate']
        available = [c for c in cols if c in listings_wn.columns]
        listings_final = listings_wn[available].drop_duplicates(subset=['listing_id'])
        # truncate and upsert
        with wh_engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE airbnb_listing RESTART IDENTITY CASCADE;"))
        upsert_dataframe(listings_final, "airbnb_listing", wh_engine, if_exists="append")
    else:
        print("No listings to load into airbnb_listing.")

    # Load monthly_airbnb fact
    if not monthly.empty:
        # parse date column to period and map to date_id
        monthly['date_parsed'] = pd.to_datetime(monthly['date'], errors='coerce', format=None)
        monthly['date_parsed'] = monthly['date_parsed'].dt.to_period('M').dt.to_timestamp()
        # join with date dim
        date_dim = pd.read_sql('SELECT date_id, date_actual FROM "date"', wh_engine)
        date_dim['date_actual'] = pd.to_datetime(date_dim['date_actual']).dt.to_period('M').dt.to_timestamp()
        monthly = monthly.merge(date_dim, left_on='date_parsed', right_on='date_actual', how='left')
        # ensure listing_id numeric
        monthly['listing_id'] = pd.to_numeric(monthly['listing_id'], errors='coerce').astype('Int64')
        # map country_id was done earlier; ensure column exists
        if 'country_id' not in monthly.columns and 'country_id_x' in monthly.columns:
            monthly['country_id'] = monthly['country_id_x']
        # select and rename fields to match warehouse schema
        monthly_final_cols = {
            'listing_id': 'listing_id',
            'date_id': 'date_id',
            'country_id': 'country_id',
            'vacant_days': 'vacant_days',
            'reserved_days': 'reserved_days',
            'length_of_stay_avg': 'avg_length_of_stay',
            'occupancy': 'occupancy',
            'rate_avg': 'rate_avg',
            'native_revenue': 'native_revenue'
        }
        monthly_final = monthly.rename(columns=monthly_final_cols)
        available = [c for c in monthly_final_cols.values() if c in monthly_final.columns]
        monthly_final = monthly_final[available].dropna(subset=['listing_id','date_id'], how='any')
        # truncate and load
        with wh_engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE monthly_airbnb RESTART IDENTITY CASCADE;"))
        upsert_dataframe(monthly_final, "monthly_airbnb", wh_engine, if_exists="append")
    else:
        print("No monthly data to load into monthly_airbnb.")

    # Load tourism (country-level yearly)
    if not tourism.empty:
        # use country_id column after mapping
        tourism['year'] = pd.to_numeric(tourism['year'], errors='coerce').astype('Int64')
        # keep required columns
        tourism_final = tourism.rename(columns={
            'total_arrivals': 'total_arrivals',
            'total_departures': 'total_departures',
            'tourism_expenditure': 'tourism_expenditure',
            'arrivals_personal': 'arrivals_personal',
            'arrivals_business': 'arrivals_business'
        })
        # ensure country_id present
        if 'country_id' in tourism_final.columns:
            tourism_final = tourism_final[['country_id','year','total_arrivals','total_departures','tourism_expenditure','arrivals_personal','arrivals_business']]
            with wh_engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE tourism RESTART IDENTITY CASCADE;"))
            upsert_dataframe(tourism_final, "tourism", wh_engine, if_exists="append")
        else:
            print("tourism data missing country_id mapping; skipping load.")
    else:
        print("No tourism data to load.")

    # Load weather_normals (country, month)
    if not weather.empty:
        # map month strings to numeric if necessary
        if 'month' in weather.columns and weather['month'].dtype == object:
            # attempt parse as month names
            weather['month_num'] = pd.to_datetime(weather['month'], format='%B', errors='coerce').dt.month
            # also try YYYY-MM or numeric strings
            weather['month_num'] = weather['month_num'].fillna(pd.to_datetime(weather['month'], errors='coerce').dt.month)
        else:
            weather['month_num'] = pd.to_numeric(weather['month'], errors='coerce').astype('Int64')
        weather['month'] = weather['month_num']
        weather_final_cols = ['country_id','month','min_temp','mean_temp','max_temp','precipitation','hours_of_sunshine']
        available = [c for c in weather_final_cols if c in weather.columns]
        weather_final = weather[available]
        with wh_engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE weather_normals RESTART IDENTITY CASCADE;"))
        upsert_dataframe(weather_final, "weather_normals", wh_engine, if_exists="append")
    else:
        print("No weather data to load.")

    print("ETL finished successfully.")

def table_exists(engine, table_name):
    try:
        q = text("SELECT to_regclass(:t) IS NOT NULL AS exists")
        with engine.connect() as conn:
            r = conn.execute(q, {"t": table_name}).scalar()
            return bool(r)
    except Exception:
        return False
    

def main():
    SRC = os.getenv("SOURCE_DB_URL")
    WH = os.getenv("WAREHOUSE_DB_URL")
    if not SRC or not WH:
        print("ERROR: SOURCE_DB_URL and WAREHOUSE_DB_URL environment variables must be set.")
        sys.exit(2)

    if not wait_for_db(SRC, name="source_db"):
        sys.exit(3)
    if not wait_for_db(WH, name="warehouse_db"):
        sys.exit(4)

    src_engine = create_engine(SRC)
    wh_engine = create_engine(WH)

    # 1) Load CSVs into source_db staging tables
    load_csvs_to_source(src_engine)

    # 2) Transform & load into warehouse_db
    transform_and_load(src_engine, wh_engine)

    src_engine.dispose()
    wh_engine.dispose()

if __name__ == "__main__":
    main()