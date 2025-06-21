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

CREATE TABLE IF NOT EXISTS public.analysis_summary (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    analysis_time TIMESTAMP DEFAULT NOW(),
    source VARCHAR(255) NOT NULL,
    summary_json JSONB NOT NULL,
    CONSTRAINT analysis_summary_run_id_source_key UNIQUE (run_id, source)
);

CREATE TABLE IF NOT EXISTS public.analysis_group_stats (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    source VARCHAR(255) NOT NULL,
    group_type VARCHAR(32),
    group_value VARCHAR(255),
    stats_json JSONB NOT NULL,
    CONSTRAINT analysis_group_stats_run_id_source_fkey
        FOREIGN KEY (run_id, source)
        REFERENCES public.analysis_summary(run_id, source)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.analysis_trends (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL,
    source VARCHAR(255) NOT NULL,
    trend_type VARCHAR(64),
    trend_json JSONB NOT NULL,
    CONSTRAINT analysis_trends_run_id_source_fkey
        FOREIGN KEY (run_id, source)
        REFERENCES public.analysis_summary(run_id, source)
        ON DELETE CASCADE
);
