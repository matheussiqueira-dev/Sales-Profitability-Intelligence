CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_key integer PRIMARY KEY, full_date date NOT NULL UNIQUE,
    day integer NOT NULL, month integer NOT NULL, month_name text NOT NULL,
    quarter integer NOT NULL, year integer NOT NULL, week_of_year integer NOT NULL,
    is_weekend boolean NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.dim_customer (
    customer_key integer PRIMARY KEY, customer_id integer NOT NULL UNIQUE,
    customer_name text NOT NULL, customer_type text NOT NULL, segment text NOT NULL,
    city text NOT NULL, state text NOT NULL, region text NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.dim_product (
    product_key integer PRIMARY KEY, product_id integer NOT NULL UNIQUE,
    product_name text NOT NULL, category text NOT NULL, subcategory text NOT NULL,
    supplier text NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics.dim_channel (
    channel_key integer PRIMARY KEY, channel_name text NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS analytics.dim_seller (
    seller_key integer PRIMARY KEY, seller_id integer NOT NULL UNIQUE,
    seller_name text NOT NULL, region text NOT NULL
);
