CREATE TABLE d_country (
    country_id SERIAL PRIMARY KEY,
    country_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE d_city (
    city_id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    country_id INT NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    FOREIGN KEY (country_id) REFERENCES d_country(country_id)
);

CREATE TABLE d_listing_type (
    listing_type_id SERIAL PRIMARY KEY,
    listing_type_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE d_room_type (
    room_type_id SERIAL PRIMARY KEY,
    room_type_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE d_currency (
    currency_id SERIAL PRIMARY KEY,
    currency_code VARCHAR(10) UNIQUE NOT NULL
);

CREATE TABLE d_date (
    date_id SERIAL PRIMARY KEY,
    date_actual DATE NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    month_name VARCHAR(15),
    quarter INT
);


CREATE TABLE airbnb_listing (
    listing_id BIGINT PRIMARY KEY,
    listing_name VARCHAR(255),
    city_id INT NOT NULL,
    listing_type_id INT NOT NULL,
    room_type_id INT NOT NULL,
    currency_id INT NOT NULL,
    guest_count INT,
    bedroom_count INT,
    beds_count INT,
    cancellation_policy VARCHAR(100),
    rating_overall DECIMAL(4,2),
    ttm_revenue DECIMAL(15,2),
    ttm_avg_rate DECIMAL(15,2),
    FOREIGN KEY (city_id) REFERENCES d_city(city_id),
    FOREIGN KEY (listing_type_id) REFERENCES d_listing_type(listing_type_id),
    FOREIGN KEY (room_type_id) REFERENCES d_room_type(room_type_id),
    FOREIGN KEY (currency_id) REFERENCES d_currency(currency_id)
);


CREATE TABLE airbnb_monthly (
    listing_id BIGINT NOT NULL,
    date_id INT NOT NULL,
    vacant_days INT,
    reserved_days INT,
    avg_length_of_stay DECIMAL(5,2),
    occupancy DECIMAL(5,2),
    rate_avg DECIMAL(15,2),
    native_revenue DECIMAL(15,2),
    PRIMARY KEY (listing_id, date_id),
    FOREIGN KEY (listing_id) REFERENCES airbnb_listing(listing_id),
    FOREIGN KEY (date_id) REFERENCES d_date(date_id)
);


CREATE TABLE tourism_stats (
    country_id INT NOT NULL,
    year INT NOT NULL,
    total_arrivals BIGINT,
    total_departures BIGINT,
    tourism_expenditure DECIMAL(15,2),
    arrivals_personal BIGINT,
    arrivals_business BIGINT,
    PRIMARY KEY (country_id, year),
    FOREIGN KEY (country_id) REFERENCES d_country(country_id)
);


CREATE TABLE weather_normals (
    country_id INT NOT NULL,
    month INT NOT NULL,
    avg_temperature DECIMAL(5,2),
    avg_precipitation DECIMAL(6,2),
    avg_humidity DECIMAL(5,2),
    avg_wind_speed DECIMAL(5,2),
    PRIMARY KEY (country_id, month),
    FOREIGN KEY (country_id) REFERENCES d_country(country_id)
);
