CREATE TABLE listings_data (
    listing_id TEXT PRIMARY KEY,
    listing_name TEXT,
    country TEXT,
    city TEXT,
    listing_type TEXT,
    room_type TEXT,
    currency TEXT,
    guests FLOAT,
    bedrooms FLOAT,
    cancellation_policy TEXT,
    rating_overall FLOAT,
    ttm_revenue FLOAT,
    ttm_avg_rate FLOAT
);

CREATE TABLE monthly_airbnb_data (
    listing_id BIGINT,
    country TEXT,
    city TEXT,
    date DATE,
    vacant_days INT,
    reserved_days INT,
    length_of_stay_avg FLOAT,
    occupancy FLOAT,
    rate_avg FLOAT,
    native_revenue FLOAT,
    revenue FLOAT
);

CREATE TABLE tourism_data (
    country TEXT,
    year INT,
    total_arrivals FLOAT,
    arrivals_personal FLOAT,
    arrivals_business FLOAT,
    tourism_expenditure FLOAT,
    total_departures FLOAT
);

CREATE TABLE weather_data (
    country TEXT,
    month TEXT,
    min_temp FLOAT,
    mean_temp FLOAT,
    max_temp FLOAT,
    precipitation FLOAT,
    hours_of_sunshine FLOAT
);
