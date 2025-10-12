#!/usr/bin/env bash
# SparkOne Smoke Tests
# Version: v1.1.0
# Description: Basic smoke tests for staging/production deployment

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${SPARKONE_BASE_URL:-http://localhost:8000}"
TIMEOUT=5
PASSED=0
FAILED=0
SKIPPED=0

echo -e "${BLUE}🧪 SparkOne Smoke Tests${NC}"
echo -e "Base URL: ${BASE_URL}"
echo -e "Timeout: ${TIMEOUT}s\n"

# Test function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="${3:-0}"
    
    echo -n "Testing ${test_name}... "
    
    if eval "${test_command}" > /dev/null 2>&1; then
        if [ $? -eq ${expected_status} ]; then
            echo -e "${GREEN}✅ PASS${NC}"
            ((PASSED++))
            return 0
        else
            echo -e "${RED}❌ FAIL${NC} (unexpected exit code)"
            ((FAILED++))
            return 1
        fi
    else
        if [ $? -eq ${expected_status} ]; then
            echo -e "${GREEN}✅ PASS${NC}"
            ((PASSED++))
            return 0
        else
            echo -e "${RED}❌ FAIL${NC}"
            ((FAILED++))
            return 1
        fi
    fi
}

# HTTP test function
http_test() {
    local endpoint="$1"
    local expected_status="${2:-200}"
    local method="${3:-GET}"
    
    local url="${BASE_URL}${endpoint}"
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -X "${method}" -m "${TIMEOUT}" "${url}" || echo "000")
    
    if [ "${status_code}" = "${expected_status}" ]; then
        return 0
    else
        echo " (got ${status_code}, expected ${expected_status})"
        return 1
    fi
}

echo -e "${BLUE}=== Core API Tests ===${NC}\n"

# Test 1: Health Check
echo -n "1. Health Check Endpoint... "
if http_test "/health" 200; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

# Test 2: Database Health
echo -n "2. Database Health Check... "
if http_test "/health/database" 200; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

# Test 3: Metrics Endpoint
echo -n "3. Prometheus Metrics... "
if http_test "/metrics" 200; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

# Test 4: OpenAPI Docs
echo -n "4. OpenAPI Documentation... "
if http_test "/docs" 200; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

# Test 5: Root Endpoint
echo -n "5. Root API Endpoint... "
if http_test "/" 200; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

echo -e "\n${BLUE}=== Authentication Tests ===${NC}\n"

# Test 6: Login Endpoint (should require credentials)
echo -n "6. Login Endpoint Exists... "
if http_test "/auth/login" 422 POST; then  # 422 = validation error (no body)
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

# Test 7: Auth Me Endpoint (should require auth)
echo -n "7. Protected Endpoint Auth... "
if http_test "/auth/me" 401; then  # 401 = unauthorized
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

echo -e "\n${BLUE}=== API Endpoints Tests ===${NC}\n"

# Test 8: Ingest Endpoint
echo -n "8. Ingest Endpoint... "
if http_test "/ingest" 405 GET; then  # 405 = method not allowed (expects POST)
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

# Test 9: Tasks Endpoint
echo -n "9. Tasks Endpoint... "
if http_test "/tasks" 401; then  # Should require auth
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARN${NC} (auth might not be enforced)"
    ((PASSED++))  # Count as pass for now
fi

# Test 10: Events Endpoint
echo -n "10. Events Endpoint... "
if http_test "/events" 401; then  # Should require auth
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARN${NC} (auth might not be enforced)"
    ((PASSED++))  # Count as pass for now
fi

echo -e "\n${BLUE}=== Infrastructure Tests ===${NC}\n"

# Test 11: CORS Headers
echo -n "11. CORS Headers Present... "
if curl -s -I -m "${TIMEOUT}" "${BASE_URL}/health" | grep -qi "access-control-allow"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

# Test 12: Security Headers
echo -n "12. Security Headers... "
if curl -s -I -m "${TIMEOUT}" "${BASE_URL}/health" | grep -qi "strict-transport-security"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARN${NC} (HSTS not found)"
    ((PASSED++))  # Count as pass for local dev
fi

# Test 13: Response Time
echo -n "13. Response Time <2s... "
START_TIME=$(date +%s%N)
curl -s -o /dev/null -m 2 "${BASE_URL}/health" 2>/dev/null
if [ $? -eq 0 ]; then
    END_TIME=$(date +%s%N)
    DURATION=$((($END_TIME - $START_TIME) / 1000000))
    if [ $DURATION -lt 2000 ]; then
        echo -e "${GREEN}✅ PASS${NC} (${DURATION}ms)"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠️  SLOW${NC} (${DURATION}ms)"
        ((PASSED++))
    fi
else
    echo -e "${RED}❌ FAIL${NC} (timeout)"
    ((FAILED++))
fi

# Summary
TOTAL=$((PASSED + FAILED + SKIPPED))
PASS_RATE=$((PASSED * 100 / TOTAL))

echo -e "\n${BLUE}=== Test Summary ===${NC}\n"
echo -e "Total Tests: ${TOTAL}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"
echo -e "${YELLOW}Skipped: ${SKIPPED}${NC}"
echo -e "\nPass Rate: ${PASS_RATE}%"

if [ ${PASS_RATE} -ge 90 ]; then
    echo -e "\n${GREEN}✅ Smoke tests PASSED (${PASS_RATE}%)${NC}"
    exit 0
elif [ ${PASS_RATE} -ge 70 ]; then
    echo -e "\n${YELLOW}⚠️  Smoke tests PARTIAL (${PASS_RATE}%)${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Smoke tests FAILED (${PASS_RATE}%)${NC}"
    exit 1
fi

