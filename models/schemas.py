"""SQLAlchemy ORM models and Pydantic schemas for ChainTrack."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, ForeignKey, Boolean,
)
from sqlalchemy.orm import relationship

from models.database import Base


# ── Helpers ───────────────────────────────────────────────────────────────


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


# ── SQLAlchemy ORM Models ─────────────────────────────────────────────────


class Product(Base):
    __tablename__ = "products"

    id = Column(String(12), primary_key=True, default=_new_id)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True, nullable=False)
    category = Column(String(100), nullable=False, default="general")
    description = Column(Text, default="")
    manufacturer = Column(String(200), default="")
    weight_kg = Column(Float, default=0.0)
    created_at = Column(DateTime, default=_utcnow)
    tracking_id = Column(String(20), unique=True, nullable=False)
    qr_data = Column(Text, default="")
    current_stage = Column(String(50), default="manufactured")
    is_active = Column(Boolean, default=True)

    chain_blocks = relationship(
        "ChainBlock", back_populates="product",
        order_by="ChainBlock.block_index",
    )
    shipments = relationship("Shipment", back_populates="product")

    def __repr__(self) -> str:
        return f"<Product {self.sku} ({self.tracking_id})>"


class ChainBlock(Base):
    __tablename__ = "chain_blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String(12), ForeignKey("products.id"), nullable=False)
    block_index = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=_utcnow)
    event_type = Column(String(50), nullable=False)
    event_data = Column(Text, default="{}")
    location = Column(String(300), default="")
    actor = Column(String(200), default="")
    previous_hash = Column(String(64), nullable=False)
    block_hash = Column(String(64), nullable=False)
    nonce = Column(Integer, default=0)

    product = relationship("Product", back_populates="chain_blocks")

    def __repr__(self) -> str:
        return f"<ChainBlock #{self.block_index} [{self.event_type}]>"


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(String(12), primary_key=True, default=_new_id)
    product_id = Column(String(12), ForeignKey("products.id"), nullable=False)
    origin = Column(String(300), nullable=False)
    destination = Column(String(300), nullable=False)
    carrier = Column(String(200), default="")
    tracking_number = Column(String(100), default="")
    status = Column(String(50), default="pending")
    estimated_arrival = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    product = relationship("Product", back_populates="shipments")

    def __repr__(self) -> str:
        return f"<Shipment {self.id} [{self.status}]>"


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    address = Column(String(500), default="")
    city = Column(String(100), default="")
    country = Column(String(100), default="")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_type = Column(String(50), default="warehouse")

    def __repr__(self) -> str:
        return f"<Location {self.name} ({self.city})>"


# ── Pydantic Schemas ──────────────────────────────────────────────────────


class ProductCreate(BaseModel):
    name: str
    sku: str
    category: str = "general"
    description: str = ""
    manufacturer: str = ""
    weight_kg: float = 0.0


class ProductResponse(BaseModel):
    id: str
    name: str
    sku: str
    category: str
    description: str
    manufacturer: str
    weight_kg: float
    tracking_id: str
    qr_data: str
    current_stage: str
    is_active: bool
    created_at: Optional[datetime] = None
    block_count: int = 0

    model_config = {"from_attributes": True}


class ChainBlockResponse(BaseModel):
    id: int
    product_id: str
    block_index: int
    timestamp: Optional[datetime] = None
    event_type: str
    event_data: str
    location: str
    actor: str
    previous_hash: str
    block_hash: str

    model_config = {"from_attributes": True}


class ChainEventCreate(BaseModel):
    product_id: str
    event_type: str
    location: str = ""
    actor: str = ""
    event_data: str = "{}"


class ShipmentCreate(BaseModel):
    product_id: str
    origin: str
    destination: str
    carrier: str = ""
    tracking_number: str = ""
    estimated_arrival: Optional[datetime] = None


class ShipmentResponse(BaseModel):
    id: str
    product_id: str
    origin: str
    destination: str
    carrier: str
    tracking_number: str
    status: str
    estimated_arrival: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LocationCreate(BaseModel):
    name: str
    address: str = ""
    city: str = ""
    country: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_type: str = "warehouse"


class LocationResponse(BaseModel):
    id: int
    name: str
    address: str
    city: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_type: str

    model_config = {"from_attributes": True}


class VerificationResult(BaseModel):
    product_id: str
    tracking_id: str = ""
    total_blocks: int = 0
    verified_blocks: int = 0
    is_valid: bool = True
    tampered_blocks: list[int] = Field(default_factory=list)
    message: str = ""


class DashboardStats(BaseModel):
    total_products: int = 0
    total_blocks: int = 0
    total_shipments: int = 0
    total_locations: int = 0
    active_shipments: int = 0
    delivered_products: int = 0
    chain_integrity: float = 100.0
    recent_events: list[dict] = Field(default_factory=list)
    stage_counts: dict[str, int] = Field(default_factory=dict)
