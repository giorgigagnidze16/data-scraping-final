SET search_path TO public;

CREATE TABLE IF NOT EXISTS public.products_raw (
    id SERIAL PRIMARY KEY,
    source VARCHAR(255),
    category VARCHAR(255),
    title TEXT,
    price REAL,
    rating REAL,
    review_count INTEGER,
    url TEXT,
    img_url TEXT
);

CREATE TABLE IF NOT EXISTS public.products (
    id SERIAL PRIMARY KEY,
    source VARCHAR(255),
    category VARCHAR(255),
    title TEXT NOT NULL,
    price REAL NOT NULL,
    rating REAL,
    review_count INTEGER,
    url TEXT UNIQUE NOT NULL,
    img_url TEXT
);
