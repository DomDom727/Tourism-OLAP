import os
import time
import pandas as pd
from sqlalchemy import create_engine

# Delay for PostgreSQL to start up (for Docker)
time.sleep(10)

# Database connection (adjust host/port if needed)
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")  # "postgres" if using Docker compose service name
DB_PORT = os.getenv("DB_PORT", "5431")       # or 5432 if inside Docker network
DB_NAME = os.getenv("DB_NAME", "stadvdb_db")

engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

print("Connecting to database...")
conn = engine.connect()
print("Connected!")

# EXTRACT
print("\n[1] Extracting data from source files...")

# Airbnb / Airroi datasets
airbnb_listings = pd.read_csv("../data/airroi_listings.csv")
airbnb_calendar = pd.read_csv("../data/airroi_calendar.csv")

# UN Tourism dataset (Excel)
tourism = pd.read_excel("../data/tourism.xlsx")

# WMO Climate dataset
climate = pd.read_csv("../data/climate.csv")

print(f"Listings: {len(airbnb_listings)} rows")
print(f"Calendar: {len(airbnb_calendar)} rows")
print(f"Tourism: {len(tourism)} rows")
print(f"Climate: {len(climate)} rows")

# TRANSFORM
print("\n[2] Transforming data to match warehouse schema...")

# -Dimensions-

# Country
d_country = airbnb_listings[['country']].drop_duplicates().rename(columns={'country': 'country_name'})
d_country['country_name'] = d_country['country_name'].str.strip()

# City
d_city = airbnb_listings[['city', 'country']].drop_duplicates().rename(columns={'city': 'city_name'})

# Room Type
d_room_type = airbnb_listings[['room_type']].drop_duplicates().rename(columns={'room_type': 'room_type_name'})

# Listing Type
d_listing_type = airbnb_listings[['property_type']].drop_duplicates().rename(columns={'property_type': 'listing_type_name'})

# Currency
if 'currency' in airbnb_listings.columns:
    d_currency = airbnb_listings[['currency']].drop_duplicates().rename(columns={'currency': 'currency_code'})
    d_currency['convertion_rate_to_usd'] = 1.0  # Placeholder if not provided
else:
    d_currency = pd.DataFrame({'currency_code': ['USD'], 'convertion_rate_to_usd': [1.0]})

# Date
airbnb_calendar['date'] = pd.to_datetime(airbnb_calendar['date'])
d_date = pd.DataFrame({'date_actual': airbnb_calendar['date'].drop_duplicates()})
d_date['year'] = d_date['date_actual'].dt.year
d_date['month'] = d_date['date_actual'].dt.month
d_date['day'] = d_date['date_actual'].dt.day

# Weather Normals (WMO)
climate = climate.rename(columns={
    'Country': 'country_name',
    'Month': 'month',
    'Temperature': 'avg_temperature',
    'Precipitation': 'avg_precipitation',
    'Humidity': 'avg_humidity'
})
d_weather_normals = climate[['country_name', 'month', 'avg_temperature', 'avg_precipitation', 'avg_humidity']]

# --- Facts -----------------------------------------------------------

# Airbnb Listing Fact
airbnb_listing = airbnb_listings.rename(columns={
    'id': 'listing_id',
    'name': 'listing_name',
    'accommodates': 'guest_count',
    'bedrooms': 'bedroom_count',
    'beds': 'beds_count',
    'review_scores_rating': 'rating_overall',
    'price': 'ttm_avg_rate'
})[[
    'listing_id', 'listing_name', 'city', 'property_type', 'room_type', 'currency',
    'guest_count', 'bedroom_count', 'beds_count', 'rating_overall', 'ttm_avg_rate'
]]

# Airbnb Monthly Fact
airbnb_calendar['month'] = airbnb_calendar['date'].dt.month
airbnb_calendar['year'] = airbnb_calendar['date'].dt.year
airbnb_monthly = airbnb_calendar.groupby(['listing_id', 'year', 'month']).agg({
    'price': 'mean',
    'available': lambda x: (x == 't').sum(),
}).reset_index().rename(columns={
    'price': 'rate_avg',
    'available': 'vacant_days'
})
airbnb_monthly['reserved_days'] = 30 - airbnb_monthly['vacant_days']
airbnb_monthly['avg_length_of_stay'] = 3.5  # placeholder
airbnb_monthly['occupancy'] = (airbnb_monthly['reserved_days'] / 30) * 100
airbnb_monthly['native_revenue'] = airbnb_monthly['rate_avg'] * airbnb_monthly['reserved_days']

# Tourism Stats
tourism_stats = tourism.rename(columns={
    'Country': 'country_name',
    'Year': 'year',
    'Arrivals': 'total_arrivals',
    'Departures': 'total_departures',
    'Expenditure': 'tourism_expenditure'
})[['country_name', 'year', 'total_arrivals', 'total_departures', 'tourism_expenditure']]


# LOAD
print("\n[3] Loading data into PostgreSQL...")

def load_table(df, name):
    df.to_sql(name, engine, if_exists='append', index=False)
    print(f"→ Loaded {len(df)} rows into {name}")

with engine.begin() as conn:
    # Clear tables if needed
    conn.execute(text("TRUNCATE f_monthly_airbnb, d_country_tourism, d_airbnb_listing, d_weather_normals, d_date, d_currency, d_room_type, d_listing_type, d_city, d_country RESTART IDENTITY CASCADE;"))

# Load Dimensions
load_table(d_country, "d_country")
load_table(d_city, "d_city")
load_table(d_listing_type, "d_listing_type")
load_table(d_room_type, "d_room_type")
load_table(d_currency, "d_currency")
load_table(d_date, "d_date")

# Map IDs for Facts
with engine.begin() as conn:
    df_country_map = pd.read_sql("SELECT country_id, country_name FROM d_country", conn)
    df_city_map = pd.read_sql("SELECT city_id, city_name, country_id FROM d_city", conn)
    df_currency_map = pd.read_sql("SELECT currency_id, currency_code FROM d_currency", conn)
    df_room_map = pd.read_sql("SELECT room_type_id, room_type_name FROM d_room_type", conn)
    df_listtype_map = pd.read_sql("SELECT listing_type_id, listing_type_name FROM d_listing_type", conn)

# Merge lookups into facts
airbnb_listing = airbnb_listing.merge(df_city_map, left_on='city', right_on='city_name', how='left')
airbnb_listing = airbnb_listing.merge(df_listtype_map, left_on='property_type', right_on='listing_type_name', how='left')
airbnb_listing = airbnb_listing.merge(df_room_map, left_on='room_type', right_on='room_type_name', how='left')
airbnb_listing = airbnb_listing.merge(df_currency_map, left_on='currency', right_on='currency_code', how='left')


d_airbnb_listing = airbnb_listing[[
    'listing_id', 'listing_name', 'city_id', 'listing_type_id', 'room_type_id',
    'currency_id', 'guest_count', 'bedroom_count', 'beds_count',
    'rating_overall', 'ttm_avg_rate'
]]
d_airbnb_listing['ttm_revenue'] = d_airbnb_listing['ttm_avg_rate'] * 30  # placeholder

# Weather and Tourism: map country
d_weather_normals = d_weather_normals.merge(df_country_map, on='country_name', how='left')[[
    'country_id', 'month', 'avg_temperature', 'avg_precipitation', 'avg_humidity'
]]

d_country_tourism = tourism_stats.merge(df_country_map, on='country_name', how='left')[[
    'country_id', 'year', 'total_arrivals', 'total_departures', 'tourism_expenditure'
]]

# Load Facts
load_table(d_weather_normals, "d_weather_normals")
load_table(d_airbnb_listing, "d_airbnb_listing")
load_table(d_country_tourism, "d_country_tourism")
load_table(airbnb_monthly, "f_monthly_airbnb")

print("\nsuccessful ETL!")
