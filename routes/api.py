"""REST API endpoints for ChainTrack."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from models.database import get_db
from models.schemas import (
    ProductCreate, ProductResponse, ChainBlockResponse,
    ChainEventCreate, ShipmentCreate, ShipmentResponse,
    LocationCreate, LocationResponse, VerificationResult,
    DashboardStats,
)
from services.blockchain import get_chain, verify_chain, get_chain_summary
from services.tracking import (
    create_product, get_product, get_product_by_tracking_id,
    list_products, record_event, create_shipment, list_shipments,
    create_location, list_locations, get_dashboard_stats,
)

router = APIRouter(prefix="/api", tags=["api"])


# ── Dashboard ─────────────────────────────────────────────────────────────


@router.get("/dashboard", response_model=DashboardStats)
def api_dashboard(db: Session = Depends(get_db)):
    """Return dashboard statistics."""
    return get_dashboard_stats(db)


# ── Products ──────────────────────────────────────────────────────────────


@router.get("/products", response_model=list[ProductResponse])
def api_list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List all registered products."""
    products = list_products(db, skip=skip, limit=limit)
    result = []
    for p in products:
        resp = ProductResponse.model_validate(p)
        resp.block_count = len(p.chain_blocks) if p.chain_blocks else 0
        result.append(resp)
    return result


@router.post("/products", response_model=ProductResponse, status_code=201)
def api_create_product(data: ProductCreate, db: Session = Depends(get_db)):
    """Register a new product in the supply chain."""
    product = create_product(db, data)
    resp = ProductResponse.model_validate(product)
    resp.block_count = len(product.chain_blocks) if product.chain_blocks else 0
    return resp


@router.get("/products/{product_id}", response_model=ProductResponse)
def api_get_product(product_id: str, db: Session = Depends(get_db)):
    """Get product details by internal ID."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    resp = ProductResponse.model_validate(product)
    resp.block_count = len(product.chain_blocks) if product.chain_blocks else 0
    return resp


@router.get("/track/{tracking_id}", response_model=ProductResponse)
def api_track_product(tracking_id: str, db: Session = Depends(get_db)):
    """Look up a product by its public tracking ID."""
    product = get_product_by_tracking_id(db, tracking_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Tracking ID not found")
    resp = ProductResponse.model_validate(product)
    resp.block_count = len(product.chain_blocks) if product.chain_blocks else 0
    return resp


# ── Chain ─────────────────────────────────────────────────────────────────


@router.get("/chain/{product_id}", response_model=list[ChainBlockResponse])
def api_get_chain(product_id: str, db: Session = Depends(get_db)):
    """Return the full hash chain for a product."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    chain = get_chain(db, product_id)
    return [ChainBlockResponse.model_validate(b) for b in chain]


@router.post("/chain/event", response_model=ChainBlockResponse, status_code=201)
def api_record_event(data: ChainEventCreate, db: Session = Depends(get_db)):
    """Record a new supply chain event (creates a chain block)."""
    block = record_event(
        db,
        product_id=data.product_id,
        event_type=data.event_type,
        location=data.location,
        actor=data.actor,
        event_data=data.event_data,
    )
    if block is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ChainBlockResponse.model_validate(block)


@router.get("/chain/{product_id}/summary")
def api_chain_summary(product_id: str, db: Session = Depends(get_db)):
    """Return a chain summary with verification status."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return get_chain_summary(db, product_id)


# ── Verification ──────────────────────────────────────────────────────────


@router.get("/verify/{product_id}", response_model=VerificationResult)
def api_verify_chain(product_id: str, db: Session = Depends(get_db)):
    """Verify the integrity of a product's hash chain."""
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    result = verify_chain(db, product_id)
    return VerificationResult(
        product_id=product_id,
        tracking_id=product.tracking_id,
        **result,
    )


@router.get("/verify/tracking/{tracking_id}", response_model=VerificationResult)
def api_verify_by_tracking(tracking_id: str, db: Session = Depends(get_db)):
    """Verify chain integrity using a tracking ID."""
    product = get_product_by_tracking_id(db, tracking_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Tracking ID not found")

    result = verify_chain(db, product.id)
    return VerificationResult(
        product_id=product.id,
        tracking_id=tracking_id,
        **result,
    )


# ── Shipments ─────────────────────────────────────────────────────────────


@router.get("/shipments", response_model=list[ShipmentResponse])
def api_list_shipments(
    product_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List shipments, optionally filtered by product."""
    shipments = list_shipments(db, product_id=product_id, skip=skip, limit=limit)
    return [ShipmentResponse.model_validate(s) for s in shipments]


@router.post("/shipments", response_model=ShipmentResponse, status_code=201)
def api_create_shipment(data: ShipmentCreate, db: Session = Depends(get_db)):
    """Create a new shipment for a product."""
    shipment = create_shipment(db, data)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ShipmentResponse.model_validate(shipment)


# ── Locations ─────────────────────────────────────────────────────────────


@router.get("/locations", response_model=list[LocationResponse])
def api_list_locations(db: Session = Depends(get_db)):
    """List all registered supply chain locations."""
    locations = list_locations(db)
    return [LocationResponse.model_validate(loc) for loc in locations]


@router.post("/locations", response_model=LocationResponse, status_code=201)
def api_create_location(data: LocationCreate, db: Session = Depends(get_db)):
    """Register a new supply chain location."""
    loc = create_location(db, data)
    return LocationResponse.model_validate(loc)
