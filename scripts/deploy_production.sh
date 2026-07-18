#!/bin/bash
# Titan AIO — Production Deployment Script
# Run on VPS: bash scripts/deploy_production.sh

set -e

echo "🚀 TITAN AIO — Production Deployment"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker not found. Installing...${NC}"
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}Docker installed. Please log out and back in.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose not found. Installing...${NC}"
    sudo apt-get update && sudo apt-get install -y docker-compose-plugin
fi

# Check .env file
if [ ! -f .env ]; then
    echo -e "${RED}.env file not found!${NC}"
    echo "Copy .env.example to .env and fill in your credentials:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Create data directory
mkdir -p data
mkdir -p credentials

echo -e "${YELLOW}Building production image...${NC}"
docker compose -f docker-compose.prod.yml build

echo -e "${YELLOW}Stopping existing containers...${NC}"
docker compose -f docker-compose.prod.yml down

echo -e "${YELLOW}Starting production services...${NC}"
docker compose -f docker-compose.prod.yml up -d

echo -e "${YELLOW}Waiting for health check...${NC}"
sleep 10

# Check health
if curl -f http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Titan AIO is running!${NC}"
    echo -e "${GREEN}   Dashboard: http://localhost:8080/dashboard${NC}"
    echo -e "${GREEN}   API Docs: http://localhost:8080/docs${NC}"
    echo -e "${GREEN}   Health: http://localhost:8080/health${NC}"
else
    echo -e "${RED}⚠️  Health check failed. Checking logs...${NC}"
    docker compose -f docker-compose.prod.yml logs titan --tail=20
fi

echo ""
echo "Commands:"
echo "  docker compose -f docker-compose.prod.yml logs -f    # View logs"
echo "  docker compose -f docker-compose.prod.yml restart    # Restart"
echo "  docker compose -f docker-compose.prod.yml down       # Stop"
echo "  docker compose -f docker-compose.prod.yml ps         # Status"
