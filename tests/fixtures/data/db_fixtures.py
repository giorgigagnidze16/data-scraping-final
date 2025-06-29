from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data import database


@pytest.fixture(scope='function')
def in_memory_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    TestingSession = sessionmaker(bind=engine)
    database.Base.metadata.create_all(engine)
    monkeypatch.setattr("src.data.database._engine", engine, raising=False)
    monkeypatch.setattr("src.data.database._Session", TestingSession, raising=False)
    monkeypatch.setattr("src.data.database._db_params", {}, raising=False)
    yield engine
    database.Base.metadata.drop_all(engine)


@pytest.fixture
def sample_products():
    return [
        {
            "source": "amazon",
            "category": "laptops",
            "title": "Acer Aspire 5",
            "price": 399.99,
            "rating": 4.3,
            "review_count": 1453,
            "url": "https://example.com/acer-aspire-5",
            "img_url": "https://example.com/img/acer.jpg",
            "scraped_at": datetime.utcnow()
        },
        {
            "source": "amazon",
            "category": "laptops",
            "title": "HP Pavilion",
            "price": 549.99,
            "rating": 4.1,
            "review_count": 1120,
            "url": "https://example.com/hp-pavilion",
            "img_url": "https://example.com/img/hp.jpg",
            "scraped_at": datetime.utcnow()
        }
    ]
