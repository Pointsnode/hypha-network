#!/bin/bash
# HYPHA Beta Quick Deploy Script
# Walks you through the deployment process step-by-step

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}HYPHA Beta Launch - Quick Deploy${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Error: Run this script from the hypha-project directory${NC}"
    echo "   cd /Users/agent_21/Downloads/Hypha/hypha-project"
    exit 1
fi

# Step 1: Check .env file
echo -e "${BLUE}Step 1: Checking environment configuration...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file${NC}"
fi

# Check if private key is set
if grep -q "your_private_key_here" .env; then
    echo -e "${YELLOW}⚠️  Private key not configured${NC}"
    echo ""
    echo "You need to add your testnet wallet private key to .env"
    echo ""
    echo "Options:"
    echo "  1. Edit .env manually:  nano .env"
    echo "  2. Use this script to add it now"
    echo ""
    read -p "Do you want to add your private key now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Enter your Base Sepolia testnet private key:"
        echo "(It should start with 0x and be 66 characters total)"
        read -p "Private key: " PRIVATE_KEY

        # Validate format
        if [[ ! $PRIVATE_KEY =~ ^0x[0-9a-fA-F]{64}$ ]]; then
            echo -e "${RED}❌ Invalid private key format${NC}"
            echo "Expected: 0x followed by 64 hex characters"
            exit 1
        fi

        # Update .env
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|PRIVATE_KEY=your_private_key_here|PRIVATE_KEY=$PRIVATE_KEY|" .env
        else
            sed -i "s|PRIVATE_KEY=your_private_key_here|PRIVATE_KEY=$PRIVATE_KEY|" .env
        fi

        echo -e "${GREEN}✅ Private key added to .env${NC}"
    else
        echo ""
        echo "Please add your private key to .env before continuing:"
        echo "  nano .env"
        echo ""
        echo "Replace this line:"
        echo "  PRIVATE_KEY=your_private_key_here"
        echo ""
        echo "With:"
        echo "  PRIVATE_KEY=0x1234567890abcdef..."
        echo ""
        exit 1
    fi
else
    echo -e "${GREEN}✅ Private key configured${NC}"
fi

# Step 2: Verify setup
echo ""
echo -e "${BLUE}Step 2: Verifying installation...${NC}"

if python3 verify_setup.py; then
    echo ""
    echo -e "${GREEN}✅ All checks passed!${NC}"
else
    echo ""
    echo -e "${RED}❌ Setup verification failed${NC}"
    echo "Please fix the issues above before deploying."
    exit 1
fi

# Step 3: Check balance
echo ""
echo -e "${BLUE}Step 3: Checking wallet balance...${NC}"

# Extract address from private key using cast if available
if command -v cast &> /dev/null; then
    PRIVATE_KEY=$(grep "PRIVATE_KEY=" .env | cut -d'=' -f2)
    ADDRESS=$(cast wallet address "$PRIVATE_KEY" 2>/dev/null || echo "")

    if [ -n "$ADDRESS" ]; then
        echo "Wallet address: $ADDRESS"

        BALANCE=$(cast balance "$ADDRESS" --rpc-url https://sepolia.base.org 2>/dev/null || echo "0")

        # Convert from wei to ETH (rough check)
        if [[ "$BALANCE" == "0" ]]; then
            echo -e "${RED}❌ Wallet has 0 ETH${NC}"
            echo ""
            echo "You need Base Sepolia ETH to deploy the contract."
            echo "Get testnet ETH from:"
            echo "  https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet"
            echo ""
            echo "Minimum needed: 0.05 ETH"
            exit 1
        else
            echo -e "${GREEN}✅ Wallet has ETH: $BALANCE wei${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  'cast' not found (install foundry for balance check)${NC}"
    echo "Skipping balance check - make sure you have testnet ETH!"
fi

# Step 4: Deploy
echo ""
echo -e "${BLUE}Step 4: Ready to deploy!${NC}"
echo ""
echo "This will:"
echo "  1. Compile smart contracts"
echo "  2. Deploy HyphaEscrow to Base Sepolia testnet"
echo "  3. Verify the deployment"
echo ""
read -p "Continue with deployment? (y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}Deploying to Base Sepolia...${NC}"
echo ""

# Run deployment
npm run deploy:testnet

echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Copy the deployed contract address from above"
echo "  2. Add it to .env:"
echo "     ESCROW_CONTRACT_ADDRESS=0xABC...123"
echo "  3. Run integration tests:"
echo "     python3 test_wdk_handshake.py"
echo ""
echo "See READY_TO_DEPLOY.md for full guide."
