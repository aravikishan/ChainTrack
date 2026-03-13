"""Application configuration for ChainTrack."""

import os

# Server
HOST = "0.0.0.0"
PORT = int(os.environ.get("CHAINTRACK_PORT", 8004))
DEBUG = os.environ.get("CHAINTRACK_DEBUG", "false").lower() == "true"

# Database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "instance", "chaintrack.db")
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL", f"sqlite:///{DATABASE_PATH}"
)

# Hash chain
GENESIS_HASH = "0" * 64
HASH_ALGORITHM = "sha256"

# QR codes
QR_BOX_SIZE = 10
QR_BORDER = 4
QR_BASE_URL = os.environ.get("CHAINTRACK_BASE_URL", f"http://localhost:8004")

# Supply chain stages (ordered)
SUPPLY_CHAIN_STAGES = [
    "manufactured",
    "quality_check",
    "shipped",
    "customs",
    "warehouse",
    "out_for_delivery",
    "delivered",
]

STAGE_LABELS = {
    "manufactured": "Manufactured",
    "quality_check": "Quality Check",
    "shipped": "Shipped",
    "customs": "Customs Clearance",
    "warehouse": "Warehouse",
    "out_for_delivery": "Out for Delivery",
    "delivered": "Delivered",
}

STAGE_ICONS = {
    "manufactured": "\U0001f3ed",
    "quality_check": "\u2705",
    "shipped": "\U0001f69a",
    "customs": "\U0001f6c3",
    "warehouse": "\U0001f4e6",
    "out_for_delivery": "\U0001f4e8",
    "delivered": "\u2714\ufe0f",
}

# Testing
TESTING = False
