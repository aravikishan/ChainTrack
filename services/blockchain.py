"""SHA-256 hash chain implementation for supply chain events.

Each supply chain event produces a ChainBlock whose hash is computed from:
  - block_index
  - timestamp (ISO format)
  - event_type
  - event_data
  - location
  - actor
  - previous_hash

The chain is tamper-evident: changing any field in any block invalidates
every subsequent hash in the chain.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

import config
from models.schemas import ChainBlock, Product


def compute_hash(
    block_index: int,
    timestamp: str,
    event_type: str,
    event_data: str,
    location: str,
    actor: str,
    previous_hash: str,
) -> str:
    """Compute the SHA-256 hash for a block's content."""
    payload = json.dumps(
        {
            "index": block_index,
            "timestamp": timestamp,
            "event_type": event_type,
            "event_data": event_data,
            "location": location,
            "actor": actor,
            "previous_hash": previous_hash,
        },
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_latest_block(db: Session, product_id: str) -> Optional[ChainBlock]:
    """Return the most recent block in a product's chain."""
    return (
        db.query(ChainBlock)
        .filter(ChainBlock.product_id == product_id)
        .order_by(ChainBlock.block_index.desc())
        .first()
    )


def get_chain(db: Session, product_id: str) -> list[ChainBlock]:
    """Return the full chain for a product, ordered by index."""
    return (
        db.query(ChainBlock)
        .filter(ChainBlock.product_id == product_id)
        .order_by(ChainBlock.block_index.asc())
        .all()
    )


def add_block(
    db: Session,
    product_id: str,
    event_type: str,
    event_data: str = "{}",
    location: str = "",
    actor: str = "",
) -> ChainBlock:
    """Create a new block and append it to the product's chain.

    Returns the newly created ChainBlock.
    """
    latest = get_latest_block(db, product_id)
    if latest is None:
        block_index = 0
        previous_hash = config.GENESIS_HASH
    else:
        block_index = latest.block_index + 1
        previous_hash = latest.block_hash

    now = datetime.now(timezone.utc)
    timestamp_str = now.isoformat()

    block_hash = compute_hash(
        block_index=block_index,
        timestamp=timestamp_str,
        event_type=event_type,
        event_data=event_data,
        location=location,
        actor=actor,
        previous_hash=previous_hash,
    )

    block = ChainBlock(
        product_id=product_id,
        block_index=block_index,
        timestamp=now,
        event_type=event_type,
        event_data=event_data,
        location=location,
        actor=actor,
        previous_hash=previous_hash,
        block_hash=block_hash,
    )
    db.add(block)

    # Update the product's current stage
    product = db.query(Product).filter(Product.id == product_id).first()
    if product and event_type in config.SUPPLY_CHAIN_STAGES:
        product.current_stage = event_type

    db.commit()
    db.refresh(block)
    return block


def verify_chain(db: Session, product_id: str) -> dict:
    """Walk the chain and verify every hash.

    Returns a dict with:
      - is_valid: bool
      - total_blocks: int
      - verified_blocks: int
      - tampered_blocks: list[int]   (block indices that fail)
      - message: str
    """
    chain = get_chain(db, product_id)
    if not chain:
        return {
            "is_valid": True,
            "total_blocks": 0,
            "verified_blocks": 0,
            "tampered_blocks": [],
            "message": "No blocks in chain.",
        }

    tampered: list[int] = []
    expected_prev = config.GENESIS_HASH

    for block in chain:
        # Verify previous-hash link
        if block.previous_hash != expected_prev:
            tampered.append(block.block_index)
            expected_prev = block.block_hash
            continue

        # Recompute block hash
        recomputed = compute_hash(
            block_index=block.block_index,
            timestamp=block.timestamp.isoformat() if block.timestamp else "",
            event_type=block.event_type,
            event_data=block.event_data,
            location=block.location,
            actor=block.actor,
            previous_hash=block.previous_hash,
        )
        if recomputed != block.block_hash:
            tampered.append(block.block_index)

        expected_prev = block.block_hash

    total = len(chain)
    verified = total - len(tampered)
    is_valid = len(tampered) == 0

    if is_valid:
        message = f"Chain integrity verified: all {total} blocks are valid."
    else:
        message = (
            f"TAMPER DETECTED: {len(tampered)} of {total} blocks "
            f"failed verification (indices: {tampered})."
        )

    return {
        "is_valid": is_valid,
        "total_blocks": total,
        "verified_blocks": verified,
        "tampered_blocks": tampered,
        "message": message,
    }


def get_chain_summary(db: Session, product_id: str) -> dict:
    """Return a summary of a product's chain for display."""
    chain = get_chain(db, product_id)
    verification = verify_chain(db, product_id)

    events = []
    for block in chain:
        events.append({
            "index": block.block_index,
            "event_type": block.event_type,
            "location": block.location,
            "actor": block.actor,
            "timestamp": block.timestamp.isoformat() if block.timestamp else "",
            "hash_prefix": block.block_hash[:16] + "...",
            "previous_hash_prefix": block.previous_hash[:16] + "...",
        })

    return {
        "product_id": product_id,
        "total_blocks": len(chain),
        "events": events,
        "verification": verification,
    }
