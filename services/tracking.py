"""Supply chain tracking and QR code generation service."""

from __future__ import annotations

import base64
import io
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import qrcode
from sqlalchemy.orm import Session

import config
from models.schemas import (
    Product, ChainBlock, Shipment, Location,
    ProductCreate, ShipmentCreate, LocationCreate,
    DashboardStats,
)
from services.blockchain import add_block, verify_chain


def generate_tracking_id() -> str:
    """Generate a unique tracking ID like CT-XXXXXXXX."""
    return "CT-" + uuid.uuid4().hex[:8].upper()


def generate_qr_code(data: str) -> str:
    """Generate a QR code image as a base64-encoded PNG string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=config.QR_BOX_SIZE,
        border=config.QR_BORDER,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def create_product(db: Session, data: ProductCreate) -> Product:
    """Register a new product and create the genesis block."""
    tracking_id = generate_tracking_id()
    qr_url = f"{config.QR_BASE_URL}/track/{tracking_id}"
    qr_data = generate_qr_code(qr_url)

    product = Product(
        name=data.name,
        sku=data.sku,
        category=data.category,
        description=data.description,
        manufacturer=data.manufacturer,
        weight_kg=data.weight_kg,
        tracking_id=tracking_id,
        qr_data=qr_data,
        current_stage="manufactured",
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Create genesis block
    add_block(
        db,
        product_id=product.id,
        event_type="manufactured",
        event_data=json.dumps({
            "name": data.name,
            "sku": data.sku,
            "manufacturer": data.manufacturer,
        }),
        location=data.manufacturer,
        actor="system",
    )

    return product


def get_product_by_tracking_id(
    db: Session, tracking_id: str
) -> Optional[Product]:
    """Look up a product by its public tracking ID."""
    return (
        db.query(Product)
        .filter(Product.tracking_id == tracking_id)
        .first()
    )


def get_product(db: Session, product_id: str) -> Optional[Product]:
    """Look up a product by internal ID."""
    return db.query(Product).filter(Product.id == product_id).first()


def list_products(
    db: Session, skip: int = 0, limit: int = 50
) -> list[Product]:
    """Return a paginated list of products."""
    return (
        db.query(Product)
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def record_event(
    db: Session,
    product_id: str,
    event_type: str,
    location: str = "",
    actor: str = "",
    event_data: str = "{}",
) -> Optional[ChainBlock]:
    """Record a supply chain event as a new chain block."""
    product = get_product(db, product_id)
    if product is None:
        return None

    block = add_block(
        db,
        product_id=product_id,
        event_type=event_type,
        event_data=event_data,
        location=location,
        actor=actor,
    )
    return block


def create_shipment(db: Session, data: ShipmentCreate) -> Optional[Shipment]:
    """Create a shipment record for a product."""
    product = get_product(db, data.product_id)
    if product is None:
        return None

    shipment = Shipment(
        product_id=data.product_id,
        origin=data.origin,
        destination=data.destination,
        carrier=data.carrier,
        tracking_number=data.tracking_number,
        estimated_arrival=data.estimated_arrival,
        status="in_transit",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)

    # Record the shipment as a chain event
    add_block(
        db,
        product_id=data.product_id,
        event_type="shipped",
        event_data=json.dumps({
            "carrier": data.carrier,
            "destination": data.destination,
            "tracking_number": data.tracking_number,
        }),
        location=data.origin,
        actor=data.carrier or "logistics",
    )

    return shipment


def list_shipments(
    db: Session, product_id: Optional[str] = None,
    skip: int = 0, limit: int = 50,
) -> list[Shipment]:
    """Return shipments, optionally filtered by product."""
    query = db.query(Shipment)
    if product_id:
        query = query.filter(Shipment.product_id == product_id)
    return query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()


def create_location(db: Session, data: LocationCreate) -> Location:
    """Register a supply chain location."""
    loc = Location(
        name=data.name,
        address=data.address,
        city=data.city,
        country=data.country,
        latitude=data.latitude,
        longitude=data.longitude,
        location_type=data.location_type,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def list_locations(db: Session) -> list[Location]:
    """Return all registered locations."""
    return db.query(Location).order_by(Location.name).all()


def get_dashboard_stats(db: Session) -> DashboardStats:
    """Compute dashboard statistics."""
    total_products = db.query(Product).count()
    total_blocks = db.query(ChainBlock).count()
    total_shipments = db.query(Shipment).count()
    total_locations = db.query(Location).count()

    active_shipments = (
        db.query(Shipment)
        .filter(Shipment.status == "in_transit")
        .count()
    )
    delivered_products = (
        db.query(Product)
        .filter(Product.current_stage == "delivered")
        .count()
    )

    # Stage counts
    stage_counts = {}
    for stage in config.SUPPLY_CHAIN_STAGES:
        count = (
            db.query(Product)
            .filter(Product.current_stage == stage)
            .count()
        )
        stage_counts[stage] = count

    # Recent events
    recent_blocks = (
        db.query(ChainBlock)
        .order_by(ChainBlock.timestamp.desc())
        .limit(10)
        .all()
    )
    recent_events = []
    for block in recent_blocks:
        product = db.query(Product).filter(Product.id == block.product_id).first()
        recent_events.append({
            "product_name": product.name if product else "Unknown",
            "tracking_id": product.tracking_id if product else "",
            "event_type": block.event_type,
            "location": block.location,
            "timestamp": block.timestamp.isoformat() if block.timestamp else "",
            "hash_prefix": block.block_hash[:12],
        })

    # Chain integrity sampling
    integrity = 100.0
    if total_products > 0:
        products = db.query(Product).limit(20).all()
        valid_count = 0
        for p in products:
            result = verify_chain(db, p.id)
            if result["is_valid"]:
                valid_count += 1
        integrity = (valid_count / len(products)) * 100.0

    return DashboardStats(
        total_products=total_products,
        total_blocks=total_blocks,
        total_shipments=total_shipments,
        total_locations=total_locations,
        active_shipments=active_shipments,
        delivered_products=delivered_products,
        chain_integrity=round(integrity, 1),
        recent_events=recent_events,
        stage_counts=stage_counts,
    )


def seed_database(db: Session) -> None:
    """Populate the database with sample data if empty."""
    if db.query(Product).count() > 0:
        return

    import os

    seed_path = os.path.join(config.BASE_DIR, "seed_data", "data.json")
    if not os.path.exists(seed_path):
        return

    with open(seed_path, "r") as f:
        data = json.load(f)

    # Seed locations
    for loc_data in data.get("locations", []):
        loc = Location(**loc_data)
        db.add(loc)
    db.commit()

    # Seed products and their events
    for prod_data in data.get("products", []):
        events = prod_data.pop("events", [])
        product_create = ProductCreate(**prod_data)
        product = create_product(db, product_create)

        for event in events:
            add_block(
                db,
                product_id=product.id,
                event_type=event["event_type"],
                event_data=json.dumps(event.get("data", {})),
                location=event.get("location", ""),
                actor=event.get("actor", "system"),
            )

        # Update current stage to last event
        if events:
            product.current_stage = events[-1]["event_type"]
            db.commit()
