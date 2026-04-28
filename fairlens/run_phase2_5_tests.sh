#!/bin/bash

# Phase 2.5 Reliability Testing Suite - Execution Script for Linux/Mac
# Run: ./run_phase2_5_tests.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="${SCRIPT_DIR}/tests/phase2_5"
PROJECT_ROOT="${SCRIPT_DIR}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ Phase 2.5 Reliability Testing Suite${NC}"
    echo -e "${BLUE}║ $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

print_subheader() {
    echo -e "\n${YELLOW}━━━ $1 ━━━${NC}\n"
}

check_docker() {
    print_subheader "Checking Docker"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker not found. Please install Docker.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker found${NC}"
    
    # Check if system is running
    if ! docker ps &> /dev/null; then
        echo -e "${RED}✗ Docker daemon not running. Please start Docker.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker daemon is running${NC}"
}

check_containers() {
    print_subheader "Checking Containers"
    
    REQUIRED_CONTAINERS=("fairlens_api" "fairlens_worker" "fairlens_redis")
    MISSING=0
    
    for container in "${REQUIRED_CONTAINERS[@]}"; do
        if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
            echo -e "${GREEN}✓ ${container} is running${NC}"
        else
            echo -e "${RED}✗ ${container} not found. Please start: docker compose up -d${NC}"
            MISSING=$((MISSING + 1))
        fi
    done
    
    if [ $MISSING -gt 0 ]; then
        echo -e "\n${YELLOW}To start containers:${NC}"
        echo "  cd infra/"
        echo "  docker compose up -d"
        exit 1
    fi
}

check_api_health() {
    print_subheader "Checking API Health"
    
    MAX_RETRIES=10
    RETRY=0
    
    while [ $RETRY -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ API is responsive${NC}"
            return 0
        fi
        
        RETRY=$((RETRY + 1))
        if [ $RETRY -lt $MAX_RETRIES ]; then
            echo "  Waiting for API... (attempt $RETRY/$MAX_RETRIES)"
            sleep 2
        fi
    done
    
    echo -e "${RED}✗ API is not responding. Check docker logs:${NC}"
    echo "  docker logs fairlens_api"
    exit 1
}

run_test_module() {
    local module=$1
    local description=$2
    
    print_subheader "Running: $description"
    
    cd "${TESTS_DIR}"
    
    if pytest "$module" -v --tb=short --color=yes; then
        echo -e "\n${GREEN}✓ $description passed${NC}"
        return 0
    else
        echo -e "\n${RED}✗ $description failed${NC}"
        return 1
    fi
}

main() {
    print_header "Starting Phase 2.5 Tests"
    
    # Pre-flight checks
    check_docker
    check_containers
    check_api_health
    
    # Install test dependencies if needed
    print_subheader "Installing Test Dependencies"
    pip install -q pytest pytest-asyncio httpx &> /dev/null || true
    
    # Run test suites
    FAILED=0
    
    run_test_module "test_load.py" "Load & Concurrency Testing" || FAILED=$((FAILED + 1))
    run_test_module "test_idempotency.py" "Idempotency Testing" || FAILED=$((FAILED + 1))
    run_test_module "test_recovery.py" "Failure Recovery Testing" || FAILED=$((FAILED + 1))
    run_test_module "test_chaos.py" "Chaos Testing" || FAILED=$((FAILED + 1))
    
    # Final report
    print_header "Test Execution Complete"
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All test suites passed!${NC}\n"
        echo -e "${GREEN}System is production-ready for reliability.${NC}\n"
        exit 0
    else
        echo -e "${RED}✗ $FAILED test suite(s) failed${NC}\n"
        echo -e "${YELLOW}Review logs above for failures.${NC}\n"
        exit 1
    fi
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Test interrupted${NC}"; exit 130' INT TERM

main "$@"
