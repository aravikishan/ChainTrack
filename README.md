# ChainTrack

[![CI](https://github.com/chaintrack/chaintrack/actions/workflows/ci.yml/badge.svg)](https://github.com/chaintrack/chaintrack/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> Supply chain tracking system with SHA-256 hash chain, QR code generation, and tamper detection.

---

## Overview

ChainTrack is a supply chain integrity platform that creates tamper-evident records
of every event in a product's journey from manufacturer to customer. Each supply chain
event is recorded as a block in a SHA-256 hash chain, where every block contains the
cryptographic hash of the previous block -- making unauthorized modifications immediately
detectable.

## Features

- **SHA-256 Hash Chain** -- Every supply chain event creates a cryptographically linked block
- **QR Code Generation** -- Unique QR codes for each product linking to their tracking page
- **Tamper Detection** -- Walk-and-verify algorithm detects any unauthorized chain modifications
- **Product Registry** -- Register products with unique tracking IDs and metadata
- **Supply Chain Timeline** -- Visual timeline of product journey through all stages
- **Real-time Dashboard** -- Statistics, recent events, and chain integrity monitoring
- **REST API** -- Full-featured API with interactive Swagger documentation
- **Location Tracking** -- Track products through factories, ports, customs, warehouses

## Architecture

```
chaintrack/
├── app.py                          # FastAPI entry point
├── config.py                       # Configuration and constants
├── models/
│   ├── database.py                 # SQLite + SQLAlchemy setup
│   └── schemas.py                  # ORM models + Pydantic schemas
├── routes/
│   ├── api.py                      # REST API endpoints
│   └── views.py                    # HTML-serving routes (Jinja2)
├── services/
│   ├── blockchain.py               # SHA-256 hash chain implementation
│   └── tracking.py                 # Tracking, QR generation, seeding
├── templates/                      # Jinja2 HTML templates
├── static/                         # CSS and JavaScript
├── tests/                          # Pytest test suite
└── seed_data/data.json             # Sample supply chain data
```

## Hash Chain Design

Each chain block contains:

| Field          | Description                                    |
|----------------|------------------------------------------------|
| `block_index`  | Sequential position in the product's chain     |
| `timestamp`    | ISO 8601 timestamp of the event                |
| `event_type`   | Supply chain stage (manufactured, shipped, etc)|
| `event_data`   | JSON payload with event-specific details       |
| `location`     | Where the event occurred                       |
| `actor`        | Who performed the action                       |
| `previous_hash`| SHA-256 hash of the previous block             |
| `block_hash`   | SHA-256 hash of this block's content           |

The hash is computed from a deterministic JSON serialization of all fields (sorted keys),
ensuring reproducibility during verification.

### Verification Algorithm

```
1. Start with genesis hash (64 zeros)
2. For each block in order:
   a. Check that block.previous_hash matches expected
   b. Recompute SHA-256 from block data
   c. Compare recomputed hash to stored block_hash
   d. If mismatch: mark block as tampered
3. Report: valid/invalid, tampered block indices
```

## Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/chaintrack/chaintrack.git
cd chaintrack

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running

```bash
# Option 1: Start script
chmod +x start.sh
./start.sh

# Option 2: Direct uvicorn
uvicorn app:app --host 0.0.0.0 --port 8004 --reload

# Option 3: Docker
docker-compose up --build
```

The application will be available at `http://localhost:8004`

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=term-missing
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8004/docs`
- **ReDoc**: `http://localhost:8004/redoc`

### Key Endpoints

| Method | Endpoint                         | Description                      |
|--------|----------------------------------|----------------------------------|
| GET    | `/api/dashboard`                 | Dashboard statistics             |
| GET    | `/api/products`                  | List all products                |
| POST   | `/api/products`                  | Register a new product           |
| GET    | `/api/track/{tracking_id}`       | Track product by tracking ID     |
| GET    | `/api/chain/{product_id}`        | Get full hash chain              |
| POST   | `/api/chain/event`               | Record a supply chain event      |
| GET    | `/api/verify/{product_id}`       | Verify chain integrity           |
| GET    | `/api/shipments`                 | List shipments                   |
| POST   | `/api/shipments`                 | Create a shipment                |
| GET    | `/api/locations`                 | List locations                   |
| POST   | `/api/locations`                 | Register a location              |

### Example: Register a Product

```bash
curl -X POST http://localhost:8004/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Widget Pro X200",
    "sku": "WPX-200-001",
    "category": "electronics",
    "manufacturer": "Acme Corp",
    "weight_kg": 1.5
  }'
```

### Example: Record a Supply Chain Event

```bash
curl -X POST http://localhost:8004/api/chain/event \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "<product_id>",
    "event_type": "shipped",
    "location": "Shanghai Port",
    "actor": "Maersk Logistics"
  }'
```

### Example: Verify Chain Integrity

```bash
curl http://localhost:8004/api/verify/<product_id>
```

## Supply Chain Stages

| Stage              | Description                                |
|--------------------|--------------------------------------------|
| `manufactured`     | Product has been manufactured              |
| `quality_check`    | Quality inspection completed               |
| `shipped`          | Product has left origin facility           |
| `customs`          | Customs clearance processing               |
| `warehouse`        | Product stored at distribution warehouse   |
| `out_for_delivery` | Product dispatched for final delivery      |
| `delivered`        | Product delivered to destination           |

## Technology Stack

| Component      | Technology                |
|----------------|---------------------------|
| Backend        | FastAPI 0.109             |
| Database       | SQLite + SQLAlchemy 2.0   |
| Validation     | Pydantic v2               |
| Cryptography   | SHA-256 (hashlib)         |
| QR Codes       | qrcode + Pillow           |
| Templates      | Jinja2                    |
| Testing        | pytest + httpx            |
| Server         | Uvicorn                   |

## Docker

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f chaintrack
```

## Environment Variables

| Variable             | Default              | Description         |
|----------------------|----------------------|---------------------|
| `CHAINTRACK_PORT`    | `8004`               | Server port         |
| `CHAINTRACK_DEBUG`   | `false`              | Enable debug mode   |
| `CHAINTRACK_BASE_URL`| `http://localhost:8004` | Base URL for QR codes|
| `DATABASE_URL`       | `sqlite:///...`      | Database URL        |

## License

This project is licensed under the MIT License -- see the [LICENSE](LICENSE) file for details.

---

*Built with FastAPI, SHA-256, and a commitment to supply chain transparency.*
