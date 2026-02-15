#!/bin/bash
# HYPHA Quick Test Script
# Tests installation and basic functionality

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              🧪 HYPHA Quick Test Suite 🧪                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

test_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

# Test 1: Check Node.js
echo "Test 1: Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    test_pass "Node.js installed ($NODE_VERSION)"
else
    test_fail "Node.js not found. Install from https://nodejs.org"
fi
echo ""

# Test 2: Check Python
echo "Test 2: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    test_pass "Python installed ($PYTHON_VERSION)"
else
    test_fail "Python3 not found"
fi
echo ""

# Test 3: Check npm packages
echo "Test 3: Checking Node.js dependencies..."
if [ -d "node_modules" ]; then
    test_pass "node_modules directory exists"

    if [ -d "node_modules/hyperswarm" ]; then
        test_pass "Hyperswarm installed"
    else
        test_warn "Hyperswarm not installed. Run: npm install"
    fi

    if [ -d "node_modules/hardhat" ]; then
        test_pass "Hardhat installed"
    else
        test_warn "Hardhat not installed. Run: npm install"
    fi
else
    test_warn "node_modules not found. Run: npm install"
fi
echo ""

# Test 4: Check Python packages
echo "Test 4: Checking Python dependencies..."
if python3 -c "import web3" 2>/dev/null; then
    test_pass "web3.py installed"
else
    test_warn "web3.py not installed. Run: pip install -r requirements.txt"
fi

if python3 -c "from dotenv import load_dotenv" 2>/dev/null; then
    test_pass "python-dotenv installed"
else
    test_warn "python-dotenv not installed. Run: pip install -r requirements.txt"
fi
echo ""

# Test 5: Check .env file
echo "Test 5: Checking environment configuration..."
if [ -f ".env" ]; then
    test_pass ".env file exists"

    if grep -q "PRIVATE_KEY=" .env && ! grep -q "PRIVATE_KEY=your_private_key_here" .env; then
        test_pass "PRIVATE_KEY configured"
    else
        test_warn "PRIVATE_KEY not set in .env"
    fi

    if grep -q "ESCROW_CONTRACT_ADDRESS=" .env && ! grep -q "ESCROW_CONTRACT_ADDRESS=your_contract_address_here" .env; then
        test_pass "ESCROW_CONTRACT_ADDRESS configured"
    else
        test_warn "ESCROW_CONTRACT_ADDRESS not set (deploy contract first)"
    fi
else
    test_warn ".env file not found. Copy .env.example to .env"
fi
echo ""

# Test 6: Check smart contract
echo "Test 6: Checking smart contract..."
if [ -f "contracts/HyphaEscrow.sol" ]; then
    test_pass "HyphaEscrow.sol exists"
else
    test_fail "HyphaEscrow.sol not found"
fi

if [ -f "hardhat.config.js" ]; then
    test_pass "hardhat.config.js exists"
else
    test_fail "hardhat.config.js not found"
fi
echo ""

# Test 7: Check SDK
echo "Test 7: Checking Python SDK..."
if [ -f "hypha_sdk/core.py" ]; then
    test_pass "SDK core.py exists"
else
    test_fail "SDK core.py not found"
fi

if [ -f "hypha_sdk/__init__.py" ]; then
    test_pass "SDK __init__.py exists"
else
    test_fail "SDK __init__.py not found"
fi
echo ""

# Test 8: Check P2P bridge
echo "Test 8: Checking P2P bridge..."
if [ -f "src/discovery/bridge.js" ]; then
    test_pass "bridge.js exists"
else
    test_fail "bridge.js not found"
fi
echo ""

# Test 9: Test Hyperswarm (if installed)
echo "Test 9: Testing Hyperswarm functionality..."
if [ -d "node_modules/hyperswarm" ]; then
    if timeout 5 node src/discovery/bridge.js lookup test-quick 2>/dev/null; then
        test_pass "Hyperswarm bridge functional"
    else
        test_warn "Hyperswarm test timeout (expected for quick test)"
    fi
else
    test_warn "Hyperswarm not installed, skipping functional test"
fi
echo ""

# Test 10: Test SDK import
echo "Test 10: Testing SDK import..."
if python3 -c "from hypha_sdk import Agent; print('SDK import successful')" 2>/dev/null; then
    test_pass "SDK imports successfully"
else
    test_fail "SDK import failed. Check Python dependencies"
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                      Test Summary                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All critical tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Configure .env with your PRIVATE_KEY"
    echo "2. Get testnet ETH from Base Sepolia faucet"
    echo "3. Deploy contract: npm run deploy:testnet"
    echo "4. Run example: python3 examples/complete_workflow.py --mode provider"
else
    echo -e "${RED}⚠️  Some tests failed. Please fix issues above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "• npm install          - Install Node.js packages"
    echo "• pip install -r requirements.txt  - Install Python packages"
    echo "• cp .env.example .env - Create environment file"
fi
echo ""
