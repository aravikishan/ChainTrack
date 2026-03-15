"""HTML-serving routes using Jinja2Templates."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from models.database import get_db
from services.blockchain import get_chain, verify_chain, get_chain_summary
from services.tracking import (
    get_product, get_product_by_tracking_id, list_products,
    get_dashboard_stats,
)
import config

router = APIRouter(tags=["views"])
templates = Jinja2Templates(directory="templates")


@router.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    """Dashboard page with supply chain overview."""
    stats = get_dashboard_stats(db)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "stage_labels": config.STAGE_LABELS,
        "stage_icons": config.STAGE_ICONS,
    })


@router.get("/products")
def products_page(request: Request, db: Session = Depends(get_db)):
    """Product registry page."""
    products = list_products(db, limit=100)
    return templates.TemplateResponse("products.html", {
        "request": request,
        "products": products,
        "stage_labels": config.STAGE_LABELS,
    })


@router.get("/track/{tracking_id}")
def track_page(
    request: Request, tracking_id: str, db: Session = Depends(get_db)
):
    """Track a product through the supply chain."""
    product = get_product_by_tracking_id(db, tracking_id)
    if product is None:
        return templates.TemplateResponse("track.html", {
            "request": request,
            "product": None,
            "chain": [],
            "summary": None,
            "tracking_id": tracking_id,
            "stages": config.SUPPLY_CHAIN_STAGES,
            "stage_labels": config.STAGE_LABELS,
            "stage_icons": config.STAGE_ICONS,
        })

    chain = get_chain(db, product.id)
    summary = get_chain_summary(db, product.id)
    return templates.TemplateResponse("track.html", {
        "request": request,
        "product": product,
        "chain": chain,
        "summary": summary,
        "tracking_id": tracking_id,
        "stages": config.SUPPLY_CHAIN_STAGES,
        "stage_labels": config.STAGE_LABELS,
        "stage_icons": config.STAGE_ICONS,
    })


@router.get("/verify")
def verify_page(request: Request, db: Session = Depends(get_db)):
    """Chain integrity verification page."""
    products = list_products(db, limit=100)
    return templates.TemplateResponse("verify.html", {
        "request": request,
        "products": products,
    })


@router.get("/about")
def about_page(request: Request):
    """About page."""
    return templates.TemplateResponse("about.html", {
        "request": request,
    })
