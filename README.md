# THE-LIMBO

Modular Monolith application for AI-driven business management.

## Project Structure

- `app/`: Main application source code
  - `core/`: Shared infrastructure (Config, DB, Security)
  - `modules/`: Business domains (Backbone, Growth, Product, CS, Advisory)
- `scripts/`: Automation scripts
- `alembic/`: Database migrations

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Setup environment variables in `.env`
3. Run the app: `uvicorn app.main:app --reload`
