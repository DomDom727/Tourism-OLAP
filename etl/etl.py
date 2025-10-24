import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text

SOURCE_DB_URL = "postgresql://postgres:postgres@source_db:5432/source_db"
WAREHOUSE_DB_URL = "postgresql://postgres:postgres@postgres:5432/stadvdb_db"

def create_connection(db_url):
    engine = create_engine(db_url)
    conn = engine.connect()
    return conn, engine

def initialize_dimensions(wh_engine):
    with wh_engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_country (
                country_id SERIAL PRIMARY KEY,
                country_name TEXT UNIQUE
            );
            CREATE TABLE IF NOT EXISTS dim_city (
                city_id SERIAL PRIMARY KEY,
                city_name TEXT,
                country_id INT REFERENCES dim_country(country_id),
                UNIQUE(city_name, country_id)
            );
            CREATE TABLE IF NOT EXISTS dim_listing (
                listing_id TEXT PRIMARY KEY,
                listing_name TEXT,
                listing_type TEXT,
                room_type TEXT,
                currency TEXT,
                guests FLOAT,
                bedrooms FLOAT,
                cancellation_policy TEXT,
                rating_overall FLOAT,
                ttm_revenue FLOAT,
                ttm_avg_rate FLOAT,
                city_id INT REFERENCES dim_city(city_id)
            );
        """))

def initialize_facts(wh_engine):
    with wh_engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_airbnb_monthly (
                id SERIAL PRIMARY KEY,
                listing_id TEXT REFERENCES dim_listing(listing_id),
                date DATE,
                vacant_days INT,
                reserved_days INT,
                length_of_stay_avg FLOAT,
                occupancy FLOAT,
                rate_avg FLOAT,
                native_revenue FLOAT,
                revenue FLOAT
            );

            CREATE TABLE IF NOT EXISTS fact_tourism (
                id SERIAL PRIMARY KEY,
                country_id INT REFERENCES dim_country(country_id),
                year INT,
                total_arrivals FLOAT,
                arrivals_personal FLOAT,
                arrivals_business FLOAT,
                tourism_expenditure FLOAT,
                total_departures FLOAT
            );

            CREATE TABLE IF NOT EXISTS fact_weather (
                id SERIAL PRIMARY KEY,
                country_id INT REFERENCES dim_country(country_id),
                month TEXT,
                min_temp FLOAT,
                mean_temp FLOAT,
                max_temp FLOAT,
                precipitation FLOAT,
                hours_of_sunshine FLOAT
            );
        """))

def load_source_tables(src_engine):
    listings = pd.read_sql("SELECT * FROM listings_data", src_engine)
    monthly = pd.read_sql("SELECT * FROM monthly_airbnb_data", src_engine)
    tourism = pd.read_sql("SELECT * FROM tourism_data", src_engine)
    weather = pd.read_sql("SELECT * FROM weather_data", src_engine)
    return listings, monthly, tourism, weather

def populate_dimensions(listings_df, wh_engine):
    with wh_engine.begin() as conn:
        # Load countries
        for country in listings_df['country'].dropna().unique():
            conn.execute(text("""
                INSERT INTO dim_country (country_name)
                VALUES (:country)
                ON CONFLICT (country_name) DO NOTHING;
            """), {"country": country})

        # Load cities
        cities = listings_df[['city', 'country']].dropna().drop_duplicates()
        for _, row in cities.iterrows():
            conn.execute(text("""
                INSERT INTO dim_city (city_name, country_id)
                SELECT :city, c.country_id FROM dim_country c
                WHERE c.country_name = :country
                ON CONFLICT (city_name, country_id) DO NOTHING;
            """), {"city": row['city'], "country": row['country']})

        # Load listings
        for _, row in listings_df.iterrows():
            conn.execute(text("""
                INSERT INTO dim_listing (
                    listing_id, listing_name, listing_type, room_type,
                    currency, guests, bedrooms, cancellation_policy,
                    rating_overall, ttm_revenue, ttm_avg_rate, city_id
                )
                SELECT
                    :listing_id, :listing_name, :listing_type, :room_type,
                    :currency, :guests, :bedrooms, :cancellation_policy,
                    :rating_overall, :ttm_revenue, :ttm_avg_rate, c.city_id
                FROM dim_city c
                JOIN dim_country d ON c.country_id = d.country_id
                WHERE c.city_name = :city AND d.country_name = :country
                ON CONFLICT (listing_id) DO NOTHING;
            """), {
                "listing_id": row['listing_id'],
                "listing_name": row['listing_name'],
                "listing_type": row['listing_type'],
                "room_type": row['room_type'],
                "currency": row['currency'],
                "guests": row['guests'],
                "bedrooms": row['bedrooms'],
                "cancellation_policy": row['cancellation_policy'],
                "rating_overall": row['rating_overall'],
                "ttm_revenue": row['ttm_revenue'],
                "ttm_avg_rate": row['ttm_avg_rate'],
                "city": row['city'],
                "country": row['country']
            })

def load_facts(monthly_df, tourism_df, weather_df, wh_engine):
    with wh_engine.begin() as conn:
        for _, row in monthly_df.iterrows():
            conn.execute(text("""
                INSERT INTO fact_airbnb_monthly (
                    listing_id, date, vacant_days, reserved_days,
                    length_of_stay_avg, occupancy, rate_avg,
                    native_revenue, revenue
                )
                VALUES (
                    :listing_id, to_date(:date, 'YYYY-MM'),
                    :vacant_days, :reserved_days, :length_of_stay_avg,
                    :occupancy, :rate_avg, :native_revenue, :revenue
                );
            """), row.to_dict())

        for _, row in tourism_df.iterrows():
            conn.execute(text("""
                INSERT INTO fact_tourism (
                    country_id, year, total_arrivals,
                    arrivals_personal, arrivals_business,
                    tourism_expenditure, total_departures
                )
                SELECT c.country_id, :year, :total_arrivals,
                       :arrivals_personal, :arrivals_business,
                       :tourism_expenditure, :total_departures
                FROM dim_country c WHERE c.country_name = :country;
            """), row.to_dict())

        for _, row in weather_df.iterrows():
            conn.execute(text("""
                INSERT INTO fact_weather (
                    country_id, month, min_temp, mean_temp,
                    max_temp, precipitation, hours_of_sunshine
                )
                SELECT c.country_id, :month, :min_temp, :mean_temp,
                       :max_temp, :precipitation, :hours_of_sunshine
                FROM dim_country c WHERE c.country_name = :country;
            """), row.to_dict())

def main():
    print("Connecting to databases...")
    src_conn, src_engine = create_connection(SOURCE_DB_URL)
    wh_conn, wh_engine = create_connection(WAREHOUSE_DB_URL)

    print("Initializing warehouse schema...")
    initialize_dimensions(wh_engine)
    initialize_facts(wh_engine)

    print("Loading data from source database...")
    listings, monthly, tourism, weather = load_source_tables(src_engine)

    print("Populating dimension tables...")
    populate_dimensions(listings, wh_engine)

    print("Loading fact tables...")
    load_facts(monthly, tourism, weather, wh_engine)

    print("ETL process complete.")

if __name__ == "__main__":
    main()