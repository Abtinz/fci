# Vision One Million Scorecard

Automated data collection for the Waterloo Region Vision One Million Scorecard using a LangGraph multi-agent pipeline, a FastAPI backend, a Streamlit testing UI, and MongoDB storage.

## Stack

- `fastapi`: API service for discovery runs and source management
- `streamlit`: workflow UI for step-by-step testing
- `mongodb`: storage for discovered sources and human-defined predefined sources

## What It Does

The pipeline is designed to:

1. discover public data sources for scorecard initiatives
2. extract metrics from those sources
3. validate extracted values
4. map results to scorecard statuses
5. persist source knowledge for reuse

Discovery now supports both:

- predefined sources from static config and human-in-the-loop Mongo entries
- dynamic Tavily-based discovery

## Services

### FastAPI

Main app:

- [api/main.py](/Users/abtinzandi/Desktop/fci/api/main.py)

Useful endpoints:

- `GET /health`
- `GET /sections`
- `POST /discovery/run`
- `POST /discovery/all-sections`
- `POST /discovery/tavily-only`
- `POST /discovery/tavily-only/all-sections`
- `GET /sources/discovered`
- `GET /sources/predefined`
- `POST /sources/predefined`

Default URL:

```text
http://localhost:8000
```

### Streamlit

Main app:

- [streamlit_app.py](/Users/abtinzandi/Desktop/fci/streamlit_app.py)

Pages:

- `Discovery Agent`
- `All Sections Discovery`
- `Tavily-Only Discovery`
- `Discovered Sources Store`
- `Predefined Sources Manager`

Default URL:

```text
http://localhost:8501
```

### MongoDB

Mongo stores:

- discovered sources returned by discovery
- human-reviewed predefined sources

## Docker Run

Start the full stack:

```bash
docker compose up --build
```

Run in background:

```bash
docker compose up --build -d
```

Stop the stack:

```bash
docker compose down
```

The compose file is:

- [docker-compose.yml](/Users/abtinzandi/Desktop/fci/docker-compose.yml)

The shared image build is:

- [Dockerfile](/Users/abtinzandi/Desktop/fci/Dockerfile)

## Environment

Create `.env` from `.env.example` and fill in your API keys:

```env
OPENAI_API_KEY=...
TAVILY_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=vision-1m-scorecard
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=vision_1m
```

Inside Docker Compose, the application services automatically use:

```env
MONGODB_URI=mongodb://mongodb:27017
```

so you do not need to change the compose file.

## Local Scripts

If you want to run pieces locally outside Docker:

```bash
./run_api.sh
./run_streamlit.sh
./run.sh --single housing-4
./test_discovery.sh
```

## Source Storage

Storage helpers:

- [storage/source_store.py](/Users/abtinzandi/Desktop/fci/storage/source_store.py)

Behavior:

- discovery reads predefined sources from both static config and MongoDB
- discovery writes discovered sources into MongoDB
- Streamlit can review discovered source records
- Streamlit can add human-reviewed predefined sources

## Current Notes

- the FastAPI and Streamlit services are containerized
- Mongo-backed pages fail gracefully if Mongo is unreachable
- the pipeline still expects initiative input data such as `output.json` for full scorecard runs
- the repository is currently strongest around the discovery stage and source-management workflow
