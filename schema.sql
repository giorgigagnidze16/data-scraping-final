CREATE TABLE IF NOT EXISTS products (
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
