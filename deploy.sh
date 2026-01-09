#!/bin/bash

# LightRAG One-Click Deployment Script for Linux
# Makes deployment easy with a single command: ./deploy.sh

# Colors for better visibility
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}      LightRAG Deployment Script        ${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. Verification Step
echo -e "${GREEN}[1/4] Verifying environment...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check for Docker Compose (plugin or standalone)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}Error: Docker Compose is not installed.${NC}"
    exit 1
fi
echo "Using: $DOCKER_COMPOSE_CMD"

# 2. Setup Configuration & Directories
echo -e "${GREEN}[2/4] Setting up configuration and directories...${NC}"

# Create data directories to prevent permission issues later
mkdir -p data/rag_storage
mkdir -p data/inputs
mkdir -p data/tiktoken

# Setup config.ini if missing
if [ ! -f config.ini ]; then
    if [ -f config.ini.example ]; then
        echo "Creating config.ini from example..."
        cp config.ini.example config.ini
    else
        echo "Warning: config.ini.example not found. Creating empty config.ini..."
        touch config.ini
    fi
fi

# Setup .env if missing
if [ ! -f .env ]; then
    if [ -f env.example ]; then
        echo "Creating .env from env.example..."
        cp env.example .env
    elif [ -f .env.example ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
    else
        echo "Warning: No environment template found."
    fi
fi

# 3. Build & Run
echo -e "${GREEN}[3/4] Building and starting services...${NC}"

# Pull latest base images
$DOCKER_COMPOSE_CMD pull

# Build and start in detached mode
$DOCKER_COMPOSE_CMD up -d --build --remove-orphans

# 4. Status Check
echo -e "${GREEN}[4/4] Checking deployment status...${NC}"

if [ $? -eq 0 ]; then
    echo -e "${BLUE}========================================${NC}"
    echo -e "${GREEN}  Deployment Successful!  ${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "Use the following commands to manage the app:"
    echo -e "  - View logs:    ${DOCKER_COMPOSE_CMD} logs -f"
    echo -e "  - Stop app:     ${DOCKER_COMPOSE_CMD} down"
    echo -e "  - Restart app:  ${DOCKER_COMPOSE_CMD} restart"
else
    echo -e "${RED}Deployment failed. Please check the error messages above.${NC}"
    exit 1
fi
