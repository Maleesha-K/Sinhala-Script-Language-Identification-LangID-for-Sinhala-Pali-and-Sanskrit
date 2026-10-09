#!/bin/bash

# Ensure we are in the correct directory
cd "$(dirname "$0")"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}Starting LangID Platform Backend Services...${NC}"

# Source virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found in $(pwd)/.venv"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo -e "\n${BLUE}Shutting down services...${NC}"
    kill $(jobs -p) 2>/dev/null
    docker compose -f ../docker-compose.yml stop $SERVICES
    exit
}
trap cleanup SIGINT SIGTERM EXIT

# Start Postgres, Redis, MinIO and the Celery workers from the full-stack compose
# file (needs webapp/.env; its passwords must match backend/.env)
SERVICES="db redis minio celery_worker celery_ocr_worker celery_surya_worker"
echo -e "${BLUE}Starting infrastructure and Celery workers via Docker...${NC}"
docker compose -f ../docker-compose.yml up -d --build $SERVICES

# Start FastAPI server
echo -e "${BLUE}Starting FastAPI server...${NC}"
uvicorn app.main:app --reload --port 8000
