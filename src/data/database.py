import json
import math
from datetime import datetime

import numpy as np
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, Column, Integer, String, Float, UniqueConstraint, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.utils.logger import get_logger

logger = get_logger("database")

Base = declarative_base()


class ProductRaw(Base):
    __tablename__ = 'products_raw'
    id = Column(Integer, primary_key=True)
    source = Column(String)
    category = Column(String)
    title = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    rating = Column(Float)
    review_count = Column(Integer)
    url = Column(String, nullable=True)
    img_url = Column(String)
    scraped_at = Column(DateTime, nullable=True, default=datetime.utcnow())
    __table_args__ = (UniqueConstraint('url', name='uix_url_raw'),)


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    source = Column(String)
    category = Column(String)
    title = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    rating = Column(Float)
    review_count = Column(Integer)
    url = Column(String, nullable=False)
    img_url = Column(String)
    scraped_at = Column(DateTime, nullable=True, default=datetime.utcnow())
    __table_args__ = (UniqueConstraint('url', name='uix_url'),)


_engine = None
_Session = None
_db_params = {}


def configure_engine(host, port, user, password, dbname):
    global _engine, _Session, _db_params
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    logger.info(f"Configuring database engine: {database_url}")
    _engine = create_engine(database_url)
    _Session = sessionmaker(bind=_engine)

    _db_params = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "dbname": dbname
    }


def init_db_with_sql(schema_path="schema.sql"):
    if _engine is None or not _db_params:
        logger.error("config not loaded")
        raise Exception("db engine not configured.")
    logger.debug(f"Ensuring schema from {schema_path}...")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    try:
        conn = psycopg2.connect(
            dbname=_db_params["dbname"],
            user=_db_params["user"],
            password=_db_params["password"],
            host=_db_params["host"],
            port=_db_params["port"]
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql)
        logger.debug("Schema ensured (schema.sql executed).")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error running schema.sql: {e}")
        raise


def save_products_raw(products):
    if _Session is None:
        logger.error("Sessionmaker not configured!")
        raise Exception("DB session not configured.")
    session = _Session()
    count_inserted = 0
    for prod in products:
        p = prod.__dict__ if hasattr(prod, "__dict__") else prod
        try:
            existing = session.query(ProductRaw).filter_by(url=p.get('url')).first()
            if not existing:
                product_obj = ProductRaw(**p)
                session.add(product_obj)
                count_inserted += 1
        except Exception as e:
            logger.warning(f"Error inserting raw product ({p.get('title', '')}): {e}")
    session.commit()
    session.close()
    logger.info(f"Inserted {count_inserted} new raw products.")


def load_products_raw(as_dataframe=True):
    if _Session is None:
        logger.error("Sessionmaker not configured! Call configure_engine() first.")
        raise Exception("Database session not configured.")
    session = _Session()
    q = session.query(ProductRaw)
    df = pd.read_sql(q.statement, session.bind)
    session.close()
    logger.info(f"Loaded {len(df)} raw products from database.")
    if as_dataframe:
        return df
    return df.to_dict(orient='records')


def save_products(products):
    if _Session is None:
        logger.error("Sessionmaker not configured!")
        raise Exception("db session not configured.")
    session = _Session()
    count_inserted = 0
    for prod in products:
        p = prod.__dict__ if hasattr(prod, "__dict__") else prod
        try:
            existing = session.query(Product).filter_by(url=p.get('url')).first()
            if not existing:
                product_obj = Product(**p)
                session.add(product_obj)
                count_inserted += 1
        except Exception as e:
            logger.warning(f"Error inserting product ({p.get('title', '')}): {e}")
    session.commit()
    session.close()
    logger.info(f"Inserted {count_inserted} new products.")


def load_products(as_dataframe=True):
    if _Session is None:
        logger.error("Sessionmaker not configured! Call configure_engine() first.")
        raise Exception("Database session not configured.")
    session = _Session()
    q = session.query(Product)
    df = pd.read_sql(q.statement, session.bind)
    session.close()
    logger.info(f"Loaded {len(df)} products from database.")
    if as_dataframe:
        return df
    return df.to_dict(orient='records')


def convert_tuple_keys_to_str(obj):
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            if isinstance(k, tuple):
                k = "_".join(str(ki) for ki in k)
            new_dict[str(k)] = convert_tuple_keys_to_str(v)
        return new_dict
    elif isinstance(obj, list):
        return [convert_tuple_keys_to_str(i) for i in obj]
    else:
        return obj


def convert_for_json(obj):
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif isinstance(obj, dict):
        return {k: convert_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_json(i) for i in obj]
    else:
        return obj


def sanitize_for_json(obj):
    """Recursively replace NaN, Inf, -Inf with None, and convert DataFrames to records."""
    if isinstance(obj, pd.DataFrame):
        return sanitize_for_json(obj.to_dict(orient="records"))
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        else:
            return obj
    elif isinstance(obj, (np.floating, np.integer)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        else:
            return float(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    else:
        return obj


def save_analysis_summary(run_id, source, summary_json):
    conn = psycopg2.connect(**_db_params)
    cur = conn.cursor()
    summary_json = convert_tuple_keys_to_str(summary_json)
    summary_json = sanitize_for_json(summary_json)
    cur.execute(
        "INSERT INTO analysis_summary (run_id, source, summary_json) VALUES (%s, %s, %s)",
        (run_id, source, json.dumps(summary_json))
    )
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Saved analysis_summary for source={source}, run_id={run_id}")


def save_analysis_group_stats(run_id, group_type, group_value, source, stats_json):
    conn = psycopg2.connect(**_db_params)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO analysis_group_stats (run_id, group_type, group_value, source, stats_json) VALUES (%s, %s, %s, %s, %s)",
        (run_id, group_type, group_value, source, json.dumps(stats_json))
    )
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Saved analysis_group_stats for {group_type}={group_value}, source={source}")


def save_analysis_trends(run_id, trend_type, source, trend_json):
    conn = psycopg2.connect(**_db_params)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO analysis_trends (run_id, trend_type, source, trend_json) VALUES (%s, %s, %s, %s)",
        (run_id, trend_type, source, json.dumps(trend_json))
    )
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Saved analysis_trends for trend_type={trend_type}, source={source}")


def generate_run_id():
    """Generate a new UUID for analysis run."""
    import uuid
    return str(uuid.uuid4())
