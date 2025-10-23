CREATE TABLE country (
    country_id SERIAL PRIMARY KEY,
    country_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE date (
    date_id SERIAL PRIMARY KEY,
    date_actual DATE NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT
);

CREATE TABLE airbnb_listing (
    listing_id BIGINT PRIMARY KEY,
    listing_name VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    country_id INT NOT NULL,
    listing_type VARCHAR(50) NOT NULL,
    room_type VARCHAR(50) NOT NULL,
    currency_code CHAR(5),
    guest_count FLOAT,
    bedroom_count FLOAT,
    cancellation_policy VARCHAR(100),
    rating_overall DECIMAL(5,2),
    ttm_revenue DECIMAL(15,2),
    ttm_avg_rate DECIMAL(15,2),
    FOREIGN KEY (country_id) REFERENCES country(country_id)
);


CREATE TABLE weather_normals (
    country_id INT NOT NULL,
    month INT NOT NULL,
    mean_temp DECIMAL(12,2),
    min_temp DECIMAL(12,2),
    max_temp DECIMAL(12,2),
    precipitation DECIMAL(12,2),
    hours_of_sunshine DECIMAL(15,2),
    PRIMARY KEY (country_id, month),
    FOREIGN KEY (country_id) REFERENCES country(country_id)
);

CREATE TABLE tourism (
    country_id INT NOT NULL,
    year INT NOT NULL,
    total_arrivals BIGINT,
    total_departures BIGINT,
    tourism_expenditure DECIMAL(15,2),
    arrivals_personal BIGINT,
    arrivals_business BIGINT,
    PRIMARY KEY (country_id, year),
    FOREIGN KEY (country_id) REFERENCES country(country_id)
);


CREATE TABLE monthly_airbnb (
    listing_id BIGINT NOT NULL,
    date_id INT NOT NULL,
    country_id INT NOT NULL,
    vacant_days INT,
    reserved_days INT,
    avg_length_of_stay DECIMAL(12,2),
    occupancy DECIMAL(5,2),
    rate_avg DECIMAL(15,2),
    native_revenue DECIMAL(15,2),
    PRIMARY KEY (listing_id, date_id),
    FOREIGN KEY (listing_id) REFERENCES airbnb_listing(listing_id),
    FOREIGN KEY (date_id) REFERENCES date(date_id),
    FOREIGN KEY (country_id) REFERENCES country(country_id)
);