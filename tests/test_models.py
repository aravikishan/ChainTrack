"""Model and schema tests for ChainTrack."""

import pytest
from models.schemas import (
    Product, ChainBlock, Shipment, Location,
    ProductCreate, ProductResponse, VerificationResult,
)


class TestProductModel:
    def test_create_product_in_db(self, db_session):
        product = Product(
            id="mod001",
            name="Model Test Widget",
            sku="MTW-001",
            category="electronics",
            tracking_id="CT-MOD00001",
            current_stage="manufactured",
        )
        db_session.add(product)
        db_session.commit()

        fetched = db_session.query(Product).filter_by(id="mod001").first()
        assert fetched is not None
        assert fetched.name == "Model Test Widget"
        assert fetched.sku == "MTW-001"

    def test_product_repr(self, sample_product):
        assert "TW-001" in repr(sample_product)

    def test_product_defaults(self, db_session):
        product = Product(
            id="def001",
            name="Defaults",
            sku="DEF-001",
            tracking_id="CT-DEF00001",
        )
        db_session.add(product)
        db_session.commit()

        assert product.is_active is True
        assert product.category == "general"
        assert product.weight_kg == 0.0


class TestChainBlockModel:
    def test_chain_block_relationship(self, db_session, sample_chain):
        product = db_session.query(Product).filter_by(id="test123").first()
        assert len(product.chain_blocks) == 3
        assert product.chain_blocks[0].event_type == "manufactured"

    def test_chain_block_ordering(self, db_session, sample_chain):
        blocks = (
            db_session.query(ChainBlock)
            .filter_by(product_id="test123")
            .order_by(ChainBlock.block_index)
            .all()
        )
        for i, block in enumerate(blocks):
            assert block.block_index == i


class TestPydanticSchemas:
    def test_product_create_validation(self):
        data = ProductCreate(name="Test", sku="T-001")
        assert data.name == "Test"
        assert data.category == "general"

    def test_verification_result(self):
        result = VerificationResult(
            product_id="abc",
            total_blocks=5,
            verified_blocks=5,
            is_valid=True,
            message="All good",
        )
        assert result.is_valid is True
        assert result.tampered_blocks == []
