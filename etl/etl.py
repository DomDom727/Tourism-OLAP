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
# Map to country_id later after insert

# Room Type
d_room_type = airbnb_listings[['room_type']].drop_duplicates().rename(columns={'room_type': 'room_type_name'})

# Listing Type
d_listing_type = airbnb_listings[['property_type']].drop_duplicates().rename(columns={'property_type': 'listing_type_name'})

# Currency
if 'currency' in airbnb_listings.columns:
    d_currency = airbnb_listings[['currency']].drop_duplicates().rename(columns={'currency': 'currency_code'})
else:
    d_currency = pd.DataFrame({'currency_code': ['USD']})

# Date
airbnb_calendar['date'] = pd.to_datetime(airbnb_calendar['date'])
d_date = pd.DataFrame({'date_actual': airbnb_calendar['date'].drop_duplicates()})
d_date['year'] = d_date['date_actual'].dt.year
d_date['month'] = d_date['date_actual'].dt.month
d_date['day'] = d_date['date_actual'].dt.day
d_date['month_name'] = d_date['date_actual'].dt.strftime('%B')
d_date['quarter'] = d_date['date_actual'].dt.quarter

# -Facts-

# Airbnb Listing Fact
airbnb_listing = airbnb_listings.rename(columns={
    'id': 'listing_id',
    'name': 'listing_name',
    'accommodates': 'guest_count',
    'bedrooms': 'bedroom_count',
    'beds': 'beds_count',
    'review_scores_rating': 'rating_overall',
    'price': 'ttm_avg_rate'
})

airbnb_listing = airbnb_listing[[
    'listing_id', 'listing_name', 'city', 'property_type', 'room_type', 'currency',
    'guest_count', 'bedroom_count', 'beds_count', 'rating_overall', 'ttm_avg_rate'
]]

# Airbnb Monthly Fact (from calendar data)
airbnb_calendar['month'] = airbnb_calendar['date'].dt.month
airbnb_calendar['year'] = airbnb_calendar['date'].dt.year
airbnb_monthly = airbnb_calendar.groupby(['listing_id', 'year', 'month']).agg({
    'price': 'mean',
    'available': lambda x: (x == 't').sum(),
}).reset_index().rename(columns={
    'price': 'rate_avg',
    'available': 'vacant_days'
})

# Tourism Stats
tourism_stats = tourism.rename(columns={
    'Country': 'country_name',
    'Year': 'year',
    'Arrivals': 'total_arrivals',
    'Departures': 'total_departures',
    'Expenditure': 'tourism_expenditure'
})
tourism_stats = tourism_stats[['country_name', 'year', 'total_arrivals', 'total_departures', 'tourism_expenditure']]

# Weather Normals
climate = climate.rename(columns={
    'Country': 'country_name',
    'Month': 'month',
    'Temperature': 'avg_temperature',
    'Precipitation': 'avg_precipitation',
    'Humidity': 'avg_humidity'
})
weather_normals = climate[['country_name', 'month', 'avg_temperature', 'avg_precipitation', 'avg_humidity']]

# LOAD
print("\n[3] Loading data into PostgreSQL warehouse...")

def load_table(df, name):
    df.to_sql(name, engine, if_exists='append', index=False)
    print(f"→ Loaded {len(df)} rows into {name}")

load_table(d_country, "d_country")
load_table(d_city, "d_city")
load_table(d_room_type, "d_room_type")
load_table(d_listing_type, "d_listing_type")
load_table(d_currency, "d_currency")
load_table(d_date, "d_date")

load_table(airbnb_listing, "d_airbnb_listing")
load_table(monthly_airbnb, "f_monthly_airbnb")
load_table(country_tourism, "d_country_tourism")
load_table(weather_normals, "d_weather_normals")

print("\nsuccessful ETL!")
