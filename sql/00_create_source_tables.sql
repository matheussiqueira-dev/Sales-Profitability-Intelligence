-- Generated from CONTRACTS, committed DDL is the physical source of truth.
CREATE TABLE IF NOT EXISTS raw.customers (
    customer_id text NOT NULL,
    customer_name text NOT NULL,
    customer_type text NOT NULL,
    city text NOT NULL,
    state text NOT NULL,
    region text NOT NULL,
    registration_date text NOT NULL,
    segment text NOT NULL,
    PRIMARY KEY (customer_id)
);
CREATE TABLE IF NOT EXISTS raw.products (
    product_id text NOT NULL,
    product_name text NOT NULL,
    category text NOT NULL,
    subcategory text NOT NULL,
    unit_cost text NOT NULL,
    list_price text NOT NULL,
    supplier text NOT NULL,
    PRIMARY KEY (product_id)
);
CREATE TABLE IF NOT EXISTS raw.orders (
    order_id text NOT NULL,
    order_date text NOT NULL,
    customer_id text NOT NULL,
    channel text NOT NULL,
    seller_id text NOT NULL,
    status text NOT NULL,
    PRIMARY KEY (order_id)
);
CREATE TABLE IF NOT EXISTS raw.order_items (
    order_item_id text NOT NULL,
    order_id text NOT NULL,
    product_id text NOT NULL,
    quantity text NOT NULL,
    unit_price text NOT NULL,
    discount_percentage text NOT NULL,
    PRIMARY KEY (order_item_id)
);
CREATE TABLE IF NOT EXISTS raw.returns (
    return_id text NOT NULL,
    order_item_id text NOT NULL,
    return_date text NOT NULL,
    quantity_returned text NOT NULL,
    return_reason text NOT NULL,
    PRIMARY KEY (return_id)
);
CREATE TABLE IF NOT EXISTS raw.freight (
    order_id text NOT NULL,
    freight_charged text NOT NULL,
    freight_actual text NOT NULL,
    PRIMARY KEY (order_id)
);
CREATE TABLE IF NOT EXISTS raw.targets (
    month text NOT NULL,
    channel text NOT NULL,
    revenue_target text NOT NULL,
    margin_target_percentage text NOT NULL,
    PRIMARY KEY (month, channel)
);
CREATE TABLE IF NOT EXISTS raw.variable_costs (
    order_item_id text NOT NULL,
    payment_fee_rate text NOT NULL,
    channel_fee_rate text NOT NULL,
    commission_rate text NOT NULL,
    packaging_cost text NOT NULL,
    PRIMARY KEY (order_item_id)
);
CREATE TABLE IF NOT EXISTS staging.customers (
    customer_id integer NOT NULL CHECK(customer_id > 0),
    customer_name text NOT NULL,
    customer_type text NOT NULL,
    city text NOT NULL,
    state text NOT NULL,
    region text NOT NULL,
    registration_date date NOT NULL,
    segment text NOT NULL,
    PRIMARY KEY (customer_id)
);
CREATE TABLE IF NOT EXISTS staging.products (
    product_id integer NOT NULL CHECK(product_id > 0),
    product_name text NOT NULL,
    category text NOT NULL,
    subcategory text NOT NULL,
    unit_cost numeric(18,2) NOT NULL CHECK(unit_cost >= 0),
    list_price numeric(18,2) NOT NULL CHECK(list_price >= 0),
    supplier text NOT NULL,
    PRIMARY KEY (product_id)
);
CREATE TABLE IF NOT EXISTS staging.orders (
    order_id integer NOT NULL CHECK(order_id > 0),
    order_date date NOT NULL,
    customer_id integer NOT NULL CHECK(customer_id > 0),
    channel text NOT NULL,
    seller_id integer NOT NULL CHECK(seller_id > 0),
    status text NOT NULL,
    PRIMARY KEY (order_id)
);
CREATE TABLE IF NOT EXISTS staging.order_items (
    order_item_id integer NOT NULL CHECK(order_item_id > 0),
    order_id integer NOT NULL CHECK(order_id > 0),
    product_id integer NOT NULL CHECK(product_id > 0),
    quantity integer NOT NULL CHECK(quantity > 0),
    unit_price numeric(18,2) NOT NULL CHECK(unit_price >= 0),
    discount_percentage numeric(8,4) NOT NULL CHECK(discount_percentage >= 0 AND discount_percentage <= 1),
    PRIMARY KEY (order_item_id)
);
CREATE TABLE IF NOT EXISTS staging.returns (
    return_id integer NOT NULL CHECK(return_id > 0),
    order_item_id integer NOT NULL CHECK(order_item_id > 0),
    return_date date NOT NULL,
    quantity_returned integer NOT NULL CHECK(quantity_returned > 0),
    return_reason text NOT NULL,
    PRIMARY KEY (return_id)
);
CREATE TABLE IF NOT EXISTS staging.freight (
    order_id integer NOT NULL CHECK(order_id > 0),
    freight_charged numeric(18,2) NOT NULL CHECK(freight_charged >= 0),
    freight_actual numeric(18,2) NOT NULL CHECK(freight_actual >= 0),
    PRIMARY KEY (order_id)
);
CREATE TABLE IF NOT EXISTS staging.targets (
    month date NOT NULL,
    channel text NOT NULL,
    revenue_target numeric(18,2) NOT NULL CHECK(revenue_target >= 0),
    margin_target_percentage numeric(8,4) NOT NULL CHECK(margin_target_percentage >= 0 AND margin_target_percentage <= 1),
    PRIMARY KEY (month, channel)
);
CREATE TABLE IF NOT EXISTS staging.variable_costs (
    order_item_id integer NOT NULL CHECK(order_item_id > 0),
    payment_fee_rate numeric(8,4) NOT NULL CHECK(payment_fee_rate >= 0 AND payment_fee_rate <= 1),
    channel_fee_rate numeric(8,4) NOT NULL CHECK(channel_fee_rate >= 0 AND channel_fee_rate <= 1),
    commission_rate numeric(8,4) NOT NULL CHECK(commission_rate >= 0 AND commission_rate <= 1),
    packaging_cost numeric(18,2) NOT NULL CHECK(packaging_cost >= 0),
    PRIMARY KEY (order_item_id),
    CHECK(payment_fee_rate + channel_fee_rate + commission_rate < 1)
);
