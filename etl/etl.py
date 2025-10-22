#!/usr/bin/env python3
# etl.py — Full ETL pipeline for AirROI + UN Tourism + WMO datasets

import os
import glob
import pandas as pd
from sqlalchemy import create_engine
from functools import reduce

# SETUP CONNECTION
print("[0] Connecting to PostgreSQL...")
engine = create_engine("postgresql://postgres:postgres@localhost:5431/stadvdb_db")

# EXTRACT
print("\n[1] Extracting datasets...")

# ---- 2.1 AIRROI ----
airroi_path = "../data/Airroi/"
city_dirs = [d for d in os.listdir(airroi_path) if os.path.isdir(os.path.join(airroi_path, d))]

listings = []
calendars = []

for city in city_dirs:
    city_folder = os.path.join(airroi_path, city)
    listing_files = glob.glob(os.path.join(city_folder, "*listings.csv"))
    calendar_files = glob.glob(os.path.join(city_folder, "*calendar_rates.csv"))

    for lf in listing_files:
        df = pd.read_csv(lf)
        df["city_name"] = city
        listings.append(df)
    for cf in calendar_files:
        df = pd.read_csv(cf)
        df["city_name"] = city
        calendars.append(df)

airbnb_listings = pd.concat(listings, ignore_index=True)
airbnb_calendar = pd.concat(calendars, ignore_index=True)

print(f"AirROI listings: {len(airbnb_listings)} rows from {len(city_dirs)} cities")
print(f"AirROI calendar: {len(airbnb_calendar)} rows")

# -WMO CLIMATE-
print("\n[1.1] Extracting WMO Climate data...")
wmo_path = "../data/WMO/"
climate_files = glob.glob(os.path.join(wmo_path, "*.csv"))
climate_frames = [pd.read_csv(f) for f in climate_files]
climate = pd.concat(climate_frames, ignore_index=True)
print(f"Climate data: {len(climate)} rows")

# -UN TOURISM-
print("\n[1.2] Extracting UN Tourism datasets...")
un_base = "../data/UN_Tourism_Statistics_Database_bulk_download/"

def find_un_file(keyword):
    matches = glob.glob(os.path.join(un_base, "**", f"*{keyword}*"), recursive=True)
    return [m for m in matches if m.endswith((".csv", ".xlsx"))]

un_files = {
    "inbound_arrivals": find_un_file("inbound_arrivals"),
    "outbound_departures": find_un_file("outbound_departures"),
    "inbound_expenditure": find_un_file("inbound_expenditure"),
    "outbound_expenditure": find_un_file("outbound_expenditure"),
}

def read_any(path):
    return pd.read_excel(path) if path.endswith(".xlsx") else pd.read_csv(path)

def normalize_un(df, value_col):
    df = df.rename(columns={df.columns[0]: "country_name", df.columns[-2]: "year", df.columns[-1]: value_col})
    df = df[["country_name", "year", value_col]]
    return df

tourism_frames = []

if un_files["inbound_arrivals"]:
    df = read_any(un_files["inbound_arrivals"][0])
    tourism_frames.append(normalize_un(df, "total_arrivals"))

if un_files["outbound_departures"]:
    df = read_any(un_files["outbound_departures"][0])
    tourism_frames.append(normalize_un(df, "total_departures"))

if un_files["inbound_expenditure"]:
    df = read_any(un_files["inbound_expenditure"][0])
    tourism_frames.append(normalize_un(df, "tourism_expenditure"))

if tourism_frames:
    tourism = reduce(lambda l, r: pd.merge(l, r, on=["country_name", "year"], how="outer"), tourism_frames)
else:
    tourism = pd.DataFrame(columns=["country_name", "year", "total_arrivals", "total_departures", "tourism_expenditure"])

print(f"UN Tourism merged: {len(tourism)} rows")

# TRANSFORM
print("\n[2] Transforming datasets...")

# -Country-
d_country = airbnb_listings[["country"]].drop_duplicates().rename(columns={"country": "country_name"})

# -City-
d_city = airbnb_listings[["city_name", "country"]].drop_duplicates().rename(columns={"country": "country_name"})

# -Listing & Room Type-
d_listing_type = airbnb_listings[["property_type"]].drop_duplicates().rename(columns={"property_type": "listing_type_name"})
d_room_type = airbnb_listings[["room_type"]].drop_duplicates().rename(columns={"room_type": "room_type_name"})

# -Currency-
if "currency" in airbnb_listings.columns:
    d_currency = airbnb_listings[["currency"]].drop_duplicates().rename(columns={"currency": "currency_code"})
else:
    d_currency = pd.DataFrame({"currency_code": ["USD"]})
d_currency["convertion_rate_to_usd"] = 1.0

# -Date-
airbnb_calendar["date"] = pd.to_datetime(airbnb_calendar["date"], errors="coerce")
d_date = pd.DataFrame({"date_actual": airbnb_calendar["date"].drop_duplicates()})
d_date["year"] = d_date["date_actual"].dt.year
d_date["month"] = d_date["date_actual"].dt.month
d_date["day"] = d_date["date_actual"].dt.day

# -Weather-
weather_normals = climate.rename(columns={
    "Country": "country_name",
    "Month": "month",
    "Temperature": "normals"
})[["country_name", "month", "normals"]].dropna()

# -Airbnb Listing Fact-
airbnb_listing = airbnb_listings.rename(columns={
    "id": "listing_id",
    "name": "listing_name",
    "city_name": "city_name",
    "property_type": "listing_type_name",
    "room_type": "room_type_name",
    "currency": "currency_code",
    "accommodates": "guest_count",
    "bedrooms": "bedroom_count",
    "review_scores_rating": "rating_overall",
    "price": "ttm_avg_rate"
})[[
    "listing_id", "listing_name", "city_name", "listing_type_name", "room_type_name",
    "currency_code", "guest_count", "bedroom_count", "rating_overall", "ttm_avg_rate"
]]

# -Monthly Airbnb Fact-
airbnb_calendar["year"] = airbnb_calendar["date"].dt.year
airbnb_calendar["month"] = airbnb_calendar["date"].dt.month

f_monthly_airbnb = airbnb_calendar.groupby(["listing_id", "year", "month"], as_index=False).agg({
    "price": "mean",
    "available": lambda x: (x == "t").sum()
}).rename(columns={"price": "rate_avg", "available": "vacant_days"})



# LOAD
print("\n[3] Loading into PostgreSQL...")

table_map = {
    "d_country": d_country,
    "d_city": d_city,
    "d_listing_type": d_listing_type,
    "d_room_type": d_room_type,
    "d_currency": d_currency,
    "d_date": d_date,
    "d_weather_normals": weather_normals,
    "d_airbnb_listing": airbnb_listing,
    "d_country_tourism": tourism,
    "f_monthly_airbnb": f_monthly_airbnb
}

for name, df in table_map.items():
    df.to_sql(name, engine, if_exists="append", index=False)
    print(f"Loaded {name}: {len(df)} rows")

print("\nSuccessful ETL.")
