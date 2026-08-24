# VasoolAI

VasoolAI is an AI-powered payment recovery assistant for Indian MSMEs, automating follow-ups and interest computation per the MSMED Act.

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   Copy `.env.example` to `.env` and fill in any required actual values.
   ```bash
   cp .env.example .env
   ```

3. **Run the Backend**
   ```bash
   uvicorn backend.main:app --reload
   ```
   The API will be accessible at http://localhost:8000.
   Check health: http://localhost:8000/health

4. **Run via Docker**
   ```bash
   docker-compose up --build
   ```

## Results

*(Placeholder for model performance and backtest results)*
