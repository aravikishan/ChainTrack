"""Pytest fixtures for ChainTrack tests."""

import os
import sys
import json
import pytest

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Override config before importing anything else
os.environ["DATABASE_URL"] = "sqlite:///test_chaintrack.db"

import config
config.TESTING = True
config.SQLALCHEMY_DATABASE_URI = "sqlite:///test_chaintrack.db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base
from models.schemas import Product, ChainBlock, Shipment, Location


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory database session for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_product(db_session):
    """Create and return a sample product in the database."""
    product = Product(
        id="test123",
        name="Test Widget",
        sku="TW-001",
        category="electronics",
        description="A test product",
        manufacturer="Test Corp",
        weight_kg=1.5,
        tracking_id="CT-TEST1234",
        qr_data="",
        current_stage="manufactured",
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def sample_chain(db_session, sample_product):
    """Create a sample chain with 3 blocks."""
    import hashlib

    blocks = []
    prev_hash = "0" * 64

    events = [
        ("manufactured", "Factory A", "operator1"),
        ("shipped", "Port Shanghai", "logistics"),
        ("customs", "Customs HQ", "inspector"),
    ]

    for i, (event_type, location, actor) in enumerate(events):
        payload = json.dumps({
            "index": i,
            "timestamp": f"2024-01-0{i+1}T00:00:00+00:00",
            "event_type": event_type,
            "event_data": "{}",
            "location": location,
            "actor": actor,
            "previous_hash": prev_hash,
        }, sort_keys=True)
        block_hash = hashlib.sha256(payload.encode()).hexdigest()

        block = ChainBlock(
            product_id=sample_product.id,
            block_index=i,
            event_type=event_type,
            event_data="{}",
            location=location,
            actor=actor,
            previous_hash=prev_hash,
            block_hash=block_hash,
        )
        db_session.add(block)
        blocks.append(block)
        prev_hash = block_hash

    db_session.commit()
    return blocks


@pytest.fixture
def app_client():
    """Create a TestClient for the FastAPI app."""
    from fastapi.testclient import TestClient

    # Use in-memory DB for the app too
    from models import database
    from sqlalchemy import create_engine as ce
    from sqlalchemy.orm import sessionmaker as sm

    test_engine = ce("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sm(bind=test_engine)

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    from app import app
    app.dependency_overrides[database.get_db] = override_get_db

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
