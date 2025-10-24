import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os

WAREHOUSE_DB_URL = "postgresql://postgres:postgres@postgres:5432/stadvdb_db"

CSV_PATHS = {
    "listings": "/data/listings_data.csv",
    "monthly":  "/data/monthly_airbnb_data.csv",
    "tourism":  "/data/tourism_data.csv",
    "weather":  "/data/weather_data.csv"
}


def transform_dataframes(df_listings, df_monthly, df_tourism, df_weather):

    countries = (
        pd.concat([
            df_listings['country'],
            df_monthly['country'],
            df_tourism['country'],
            df_weather['country']
        ])
        .dropna()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    df_country = pd.DataFrame({
        'country_id': range(1, len(countries) + 1),
        'country_name': countries
    })


    df_monthly['date'] = pd.to_datetime(df_monthly['date'])
    df_date = (
        df_monthly[['date']]
        .drop_duplicates()
        .rename(columns={'date': 'date_actual'})
        .sort_values(by='date_actual')
        .reset_index(drop=True)
    )
    df_date['date_id'] = range(1, len(df_date) + 1)
    df_date['year'] = df_date['date_actual'].dt.year
    df_date['month'] = df_date['date_actual'].dt.month
    df_date['day'] = df_date['date_actual'].dt.day
    df_date = df_date[['date_id', 'date_actual', 'year', 'month', 'day']]


    df_airbnb_listing = df_listings.merge(df_country, how='left',
                                          left_on='country', right_on='country_name')

    df_airbnb_listing = df_airbnb_listing.rename(columns={
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
    })[
        ['listing_id', 'listing_name', 'city', 'country_id', 'listing_type',
         'room_type', 'currency_code', 'guest_count', 'bedroom_count',
         'cancellation_policy', 'rating_overall', 'ttm_revenue', 'ttm_avg_rate']
    ]
    df_airbnb_listing['listing_id'] = df_airbnb_listing['listing_id'].astype('int64')


    month_cols = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_map = {m: i+1 for i, m in enumerate(month_cols)}
    df_weather['month'] = df_weather['month'].map(month_map)

    df_weather_normals = df_weather.merge(df_country, how='left',
                                          left_on='country', right_on='country_name')[
        ['country_id', 'month', 'mean_temp', 'min_temp', 'max_temp',
         'precipitation', 'hours_of_sunshine']
    ]
    df_weather_normals = (df_weather_normals
                          .drop_duplicates(subset=['country_id', 'month'])
                          .sort_values(['country_id', 'month'])
                          .reset_index(drop=True))


    df_tourism_dw = df_tourism.merge(df_country, how='left',
                                     left_on='country', right_on='country_name')[
        ['country_id', 'year', 'total_arrivals', 'total_departures',
         'tourism_expenditure', 'arrivals_personal', 'arrivals_business']
    ]
    df_tourism_dw = df_tourism_dw.drop_duplicates(subset=['country_id', 'year'])


    df_monthly_airbnb = df_monthly.merge(df_country, how='left',
                                         left_on='country', right_on='country_name')
    df_monthly_airbnb = df_monthly_airbnb.merge(df_date, how='left',
                                                left_on='date', right_on='date_actual')

    df_monthly_airbnb = df_monthly_airbnb.rename(columns={
        'length_of_stay_avg': 'avg_length_of_stay'
    })[
        ['listing_id', 'date_id', 'country_id', 'vacant_days', 'reserved_days',
         'avg_length_of_stay', 'occupancy', 'rate_avg', 'native_revenue']
    ]
    df_monthly_airbnb['listing_id'] = df_monthly_airbnb['listing_id'].astype('int64')

    return {
        "country": df_country,
        "date": df_date,
        "airbnb_listing": df_airbnb_listing,
        "weather_normals": df_weather_normals,
        "tourism": df_tourism_dw,
        "monthly_airbnb": df_monthly_airbnb
    }


def load_to_warehouse(transformed_dfs, engine):
    load_order = ["country", "date", "airbnb_listing",
                  "weather_normals", "tourism", "monthly_airbnb"]

    with engine.begin() as connection:  # starts a transaction
        try:
            for table_name in load_order:
                df = transformed_dfs[table_name]
                print(f"Loading {table_name} ({len(df)} rows)...")
                df.to_sql(table_name, connection, if_exists="replace", index=False)
                print(f"Loaded {table_name} successfully.")

            print("All tables loaded successfully. Transaction committed.")
        except Exception as e:
            print(f"Error during load: {e}")
            print("Transaction rolled back automatically.")
            raise

def main():
    print("Connecting to warehouse database...")
    engine = create_engine(WAREHOUSE_DB_URL)

    print("Transforming raw dataframes...")

    df_listings = pd.read_csv("/data/listings_data.csv")
    df_monthly = pd.read_csv("/data/monthly_airbnb_data.csv")
    df_tourism = pd.read_csv("/data/tourism_data.csv")
    df_weather = pd.read_csv("/data/weather_data.csv")

    transformed_dfs = transform_dataframes(df_listings, df_monthly, df_tourism, df_weather)

    print("Loading transformed data into warehouse (transactional)...")
    load_to_warehouse(transformed_dfs, engine)

if __name__ == "__main__":
    main()
